import ArgumentParser
import Foundation
import Yams
import TOMLKit

#if canImport(FoundationNetworking)
import FoundationNetworking

#endif

#if swift(>=5.5) && !canImport(Darwin)
// Polyfill for async URLSession methods on non-Apple platforms
extension URLSession {
    func data(for request: URLRequest) async throws -> (Data, URLResponse) {
        try await withCheckedThrowingContinuation { continuation in
            let task = self.dataTask(with: request) { data, response, error in
                guard let data = data, let response = response else {
                    let error = error ?? URLError(.badServerResponse)
                    return continuation.resume(throwing: error)
                }
                continuation.resume(returning: (data, response))
            }
            task.resume()
        }
    }
}

#endif

// MARK: - Scripts Config and Runner

struct ScriptsWrapper: Codable {
    let scripts: [String: String]
}

enum ScriptsConfigSource: String {
    case yaml = "spindle.yaml"
    case json = "spindle.json"
    case pyproject = "pyproject.toml ([tool.spindle.scripts])"
}

struct ScriptsConfigLoader {
    static func loadScripts() -> (scripts: [String: String], source: ScriptsConfigSource)? {
        let fm = FileManager.default
        let cwd = URL(fileURLWithPath: fm.currentDirectoryPath)

        // 1) spindle.yaml
        let yamlURL = cwd.appendingPathComponent("spindle.yaml")
        if fm.fileExists(atPath: yamlURL.path) {
            if let scripts = loadFromYAML(yamlURL) { return (scripts, .yaml) }
        }

        // 2) spindle.json
        let jsonURL = cwd.appendingPathComponent("spindle.json")
        if fm.fileExists(atPath: jsonURL.path) {
            if let scripts = loadFromJSON(jsonURL) { return (scripts, .json) }
        }

        // 3) pyproject.toml -> [tool.spindle.scripts]
        let tomlURL = cwd.appendingPathComponent("pyproject.toml")
        if fm.fileExists(atPath: tomlURL.path) {
            if let scripts = loadFromPyProjectTOML(tomlURL) { return (scripts, .pyproject) }
        }

        return nil
    }

    private static func loadFromYAML(_ url: URL) -> [String: String]? {
        do {
            let content = try String(contentsOf: url, encoding: .utf8)
            // Prefer a typed decode first
            if let wrapper = try? YAMLDecoder().decode(ScriptsWrapper.self, from: content) {
                return wrapper.scripts
            }
            // Fallback to generic structure
            if let any = try Yams.load(yaml: content) as? [String: Any] {
                if let map = any["scripts"] as? [String: Any] {
                    var out: [String: String] = [:]
                    for (k, v) in map { if let s = v as? String { out[k] = s } }
                    return out
                }
            }
        } catch {
            // ignore and fallback
        }
        return nil
    }

    private static func loadFromJSON(_ url: URL) -> [String: String]? {
        do {
            let data = try Data(contentsOf: url)
            if let wrapper = try? JSONDecoder().decode(ScriptsWrapper.self, from: data) {
                return wrapper.scripts
            }
            // Fallback to generic dictionary
            let obj = try JSONSerialization.jsonObject(with: data, options: [])
            if let dict = obj as? [String: Any], let scripts = dict["scripts"] as? [String: Any] {
                var out: [String: String] = [:]
                for (k, v) in scripts { if let s = v as? String { out[k] = s } }
                return out
            }
        } catch {
            // ignore and fallback
        }
        return nil
    }

    private struct PyProject: Decodable {
        struct Tool: Decodable {
            struct Spindle: Decodable { let scripts: [String: String]? }
            let spindle: Spindle?
        }
        let tool: Tool?
    }

    private static func loadFromPyProjectTOML(_ url: URL) -> [String: String]? {
        do {
            let content = try String(contentsOf: url, encoding: .utf8)
            let table = try TOMLTable(string: content)
            if let py = try? TOMLDecoder().decode(PyProject.self, from: table),
               let map = py.tool?.spindle?.scripts {
                return map
            }
        } catch {
            // ignore and fallback
        }
        return nil
    }
}

enum ScriptRunner {
    @discardableResult
    static func run(script: String, extraArgs: [String]) throws -> Int32 {
        // Append extra args to the command string, quoting each arg
        let argsPart = extraArgs.map { shellEscape($0) }.joined(separator: " ")
        let command = argsPart.isEmpty ? script : script + " " + argsPart

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = ["-lc", command]
        process.currentDirectoryURL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        process.standardOutput = FileHandle.standardOutput
        process.standardError = FileHandle.standardError

        try process.run()
        process.waitUntilExit()
        return process.terminationStatus
    }

    private static func shellEscape(_ arg: String) -> String {
        if arg.isEmpty { return "''" }
        let needsQuotes = arg.contains(" ") || arg.contains("\t") || arg.contains("\n") || arg.contains("\"") || arg.contains("'") || arg.contains("$") || arg.contains("`") || arg.contains("\\")
        if !needsQuotes { return arg }
        // Use single quotes and escape single quotes by closing, inserting \' , and reopening
        let escaped = arg.replacingOccurrences(of: "'", with: "'\\''")
        return "'\(escaped)'"
    }
}

// MARK: - CLI: run and shortcut commands

struct Run: AsyncParsableCommand {
    static let configuration = CommandConfiguration(abstract: "Run a configured script from spindle.yaml/json/pyproject.toml")

    @Argument(help: "The script name to run (as defined in your config).")
    var name: String

    @Argument(parsing: .captureForPassthrough, help: "Arguments to pass to the script")
    var scriptArgs: [String] = []

    func run() async throws {
        guard let (scripts, source) = ScriptsConfigLoader.loadScripts() else {
            print("No scripts configuration found. Create spindle.yaml, spindle.json, or [tool.spindle.scripts] in pyproject.toml.")
            return
        }
        guard let script = scripts[name] else {
            print("Script '\(name)' not found in \(source.rawValue). Available: \(scripts.keys.sorted().joined(separator: ", "))")
            return
        }
        let status = try ScriptRunner.run(script: script, extraArgs: scriptArgs)
        if status != 0 { throw NSError(domain: "ScriptError", code: Int(status), userInfo: [NSLocalizedDescriptionKey: "Script exited with status \(status)"]) }
    }
}

protocol ShortcutCommand: AsyncParsableCommand {
    static var scriptName: String { get }
}

extension ShortcutCommand {
    static var configuration: CommandConfiguration {
        CommandConfiguration(commandName: Self.scriptName, abstract: "Run the '\(Self.scriptName)' script if configured")
    }

    func executeShortcut(scriptArgs: [String]) async throws {
        guard let (scripts, source) = ScriptsConfigLoader.loadScripts() else {
            print("No scripts configuration found. Create spindle.yaml, spindle.json, or [tool.spindle.scripts] in pyproject.toml.")
            return
        }
        guard let script = scripts[Self.scriptName] else {
            print("No '\(Self.scriptName)' script found in \(source.rawValue). Use 'spindle run <name>' for other scripts. Available: \(scripts.keys.sorted().joined(separator: ", "))")
            return
        }
        let status = try ScriptRunner.run(script: script, extraArgs: scriptArgs)
        if status != 0 { throw NSError(domain: "ScriptError", code: Int(status), userInfo: [NSLocalizedDescriptionKey: "Script exited with status \(status)"]) }
    }
}

struct StartCommand: ShortcutCommand {
    static let scriptName = "start"
    @Argument(parsing: .captureForPassthrough) var args: [String] = []
    func run() async throws { try await executeShortcut(scriptArgs: args) }
}

struct DevCommand: ShortcutCommand {
    static let scriptName = "dev"
    @Argument(parsing: .captureForPassthrough) var args: [String] = []
    func run() async throws { try await executeShortcut(scriptArgs: args) }
}

struct LaunchCommand: ShortcutCommand {
    static let scriptName = "launch"
    @Argument(parsing: .captureForPassthrough) var args: [String] = []
    func run() async throws { try await executeShortcut(scriptArgs: args) }
}

struct BuildCommand: ShortcutCommand {
    static let scriptName = "build"
    @Argument(parsing: .captureForPassthrough) var args: [String] = []
    func run() async throws { try await executeShortcut(scriptArgs: args) }
}

struct TestCommand: ShortcutCommand {
    static let scriptName = "test"
    @Argument(parsing: .captureForPassthrough) var args: [String] = []
    func run() async throws { try await executeShortcut(scriptArgs: args) }
}

struct DeployCommand: ShortcutCommand {
    static let scriptName = "deploy"
    @Argument(parsing: .captureForPassthrough) var args: [String] = []
    func run() async throws { try await executeShortcut(scriptArgs: args) }
}

@main
struct Spindle: AsyncParsableCommand {
    static let configuration = CommandConfiguration(
        abstract: "A tool to install components from Git repositories.",
        subcommands: [
            Install.self,
            Run.self,
            StartCommand.self,
            DevCommand.self,
            LaunchCommand.self,
            BuildCommand.self,
            TestCommand.self,
            DeployCommand.self
        ]
    )
}

// MARK: - Data Structures

struct SpindleManifest: Codable {
    let name: String
    let components: [String: ComponentDefinition]
}

struct ComponentDefinition: Codable {
    let files: [String]
    let dependencies: [String]
}

struct ComponentIdentifier {
    let user: String
    let repo: String
    let path: String

    init?(identifier: String) {
        let parts = identifier.split(separator: "/", maxSplits: 2).map(String.init)
        guard parts.count >= 2 else { return nil }
        
        self.user = parts[0]
        self.repo = parts[1]
        self.path = (parts.count > 2) ? parts[2] : "*"
    }
}

// MARK: - Command Logic

struct Install: AsyncParsableCommand {
    static let configuration = CommandConfiguration(abstract: "Install a component.")

    @Argument(help: "The component to install (e.g., GitHubUser/repo/component).")
    var componentIdentifier: String

    func run() async throws {
        guard let id = ComponentIdentifier(identifier: componentIdentifier) else {
            print("Error: Invalid component format. Expected 'GitHubUser/repo/path'.")
            return
        }

        let fileManager = FileManager.default
        let tempDir = fileManager.temporaryDirectory.appendingPathComponent("spindle-\(UUID().uuidString)")

        do {
            try fileManager.createDirectory(at: tempDir, withIntermediateDirectories: true, attributes: nil)
            defer { try? fileManager.removeItem(at: tempDir) }

            try await fetchRepository(id: id, to: tempDir)

            let manifestURL = tempDir.appendingPathComponent("spindle.json")
            let data = try Data(contentsOf: manifestURL)
            let manifest = try JSONDecoder().decode(SpindleManifest.self, from: data)

            print("Successfully fetched and parsed manifest for '\(manifest.name)'.")

            // 1. Resolve component and all its dependencies
            var filesToInstall = Set<String>()
            var visited = Set<String>()
            try resolveDependencies(for: id.path, manifest: manifest, filesToInstall: &filesToInstall, visited: &visited)

            // 2. Define destination and copy files
            let destinationRoot = URL(fileURLWithPath: fileManager.currentDirectoryPath).appendingPathComponent("spindle")
            print("Installing component(s) into '\(destinationRoot.path)'...")
            
            var installedDirectories = Set<URL>()

            for file in filesToInstall.sorted() {
                let sourceURL = tempDir.appendingPathComponent(file)
                let destinationURL = destinationRoot.appendingPathComponent(file)
                let destinationDir = destinationURL.deletingLastPathComponent()

                // Ensure destination subdirectory exists
                try fileManager.createDirectory(at: destinationDir, withIntermediateDirectories: true, attributes: nil)
                installedDirectories.insert(destinationDir)

                // Copy file, overwriting if it exists
                if fileManager.fileExists(atPath: destinationURL.path) {
                    try fileManager.removeItem(at: destinationURL)
                }
                try fileManager.copyItem(at: sourceURL, to: destinationURL)
                print("  - Copied \(file)")
            }

            // 3. Create __init__.py files to ensure Python package structure
            try createInitPyFiles(in: installedDirectories, root: destinationRoot)

            print("Installation complete.")

        } catch {
            print("Error: \(error.localizedDescription)")
        }
    }

    private func resolveDependencies(for componentName: String, manifest: SpindleManifest, filesToInstall: inout Set<String>, visited: inout Set<String>) throws {
        // Avoid circular dependencies
        if visited.contains(componentName) { return }
        visited.insert(componentName)

        guard let component = manifest.components[componentName] else {
            throw NSError(domain: "ResolverError", code: 1, userInfo: [NSLocalizedDescriptionKey: "Component '\(componentName)' not found in manifest."])
        }

        // Recursively resolve dependencies first
        for dependency in component.dependencies {
            try resolveDependencies(for: dependency, manifest: manifest, filesToInstall: &filesToInstall, visited: &visited)
        }

        // Add this component's files
        for file in component.files {
            filesToInstall.insert(file)
        }
    }

    private func fetchRepository(id: ComponentIdentifier, to directory: URL) async throws {
        if let token = ProcessInfo.processInfo.environment["GITHUB_TOKEN"] {
            do {
                print("GITHUB_TOKEN found. Attempting to download via API...")
                try await downloadAndUntar(user: id.user, repo: id.repo, token: token, to: directory)
                return
            } catch {
                print("API download failed: \(error.localizedDescription). Falling back to git clone.")
            }
        }
        
        print("Using git clone.")
        try await gitClone(user: id.user, repo: id.repo, to: directory)
    }

    private func downloadAndUntar(user: String, repo: String, token: String, to directory: URL) async throws {
        let urlString = "https://api.github.com/repos/\(user)/\(repo)/tarball/main"
        guard let url = URL(string: urlString) else { throw URLError(.badURL) }

        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let tarPath = directory.appendingPathComponent("repo.tar.gz")
        try data.write(to: tarPath)
        
        try await untar(file: tarPath, to: directory)
        try FileManager.default.removeItem(at: tarPath)
    }

    private func untar(file: URL, to directory: URL) async throws {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/tar")
                task.arguments = ["-xzf", file.path, "-C", directory.path, "--strip-components=1"]
        try task.run()
        task.waitUntilExit()
        if task.terminationStatus != 0 {
             throw NSError(domain: "UntarError", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to extract repository tarball."])
        }
    }

    private func gitClone(user: String, repo: String, to directory: URL) async throws {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/git")
        process.currentDirectoryURL = directory
        process.arguments = ["clone", "--depth", "1", "https://github.com/\(user)/\(repo).git", "."]
        
        try process.run()
        process.waitUntilExit()
        
        if process.terminationStatus != 0 {
            throw NSError(domain: "GitCloneError", code: 1, userInfo: nil)
        }
    }

    private func createInitPyFiles(in directories: Set<URL>, root: URL) throws {
        let fileManager = FileManager.default
        var allDirs = directories
        allDirs.insert(root) // Ensure the root itself is included

        var parentDirsToEnsure = Set<URL>()
        for dir in allDirs {
            var currentDir = dir
            // Walk up to the root, collecting all directories in the path
            while currentDir.path.count >= root.path.count && currentDir.path.hasPrefix(root.path) {
                parentDirsToEnsure.insert(currentDir)
                if currentDir == root { break }
                currentDir.deleteLastPathComponent()
            }
        }

        for dir in parentDirsToEnsure {
            let initPyURL = dir.appendingPathComponent("__init__.py")
            if !fileManager.fileExists(atPath: initPyURL.path) {
                fileManager.createFile(atPath: initPyURL.path, contents: nil, attributes: nil)
                let relativePath = dir.path.replacingOccurrences(of: root.deletingLastPathComponent().path, with: "")
                print("  - Created __init__.py in .\(relativePath)")
            }
        }
    }
}
