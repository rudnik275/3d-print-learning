// winctl — list on-screen windows or bring an app (by pid) to front. No Accessibility permission needed.
//   winctl windows [pid]   -> pid  windowID  name  x y w h   (only on-screen, layer 0)
//   winctl front <pid>     -> activate that process's windows
import AppKit
let args = CommandLine.arguments
if args.count >= 2 && args[1] == "windows" {
    let filter = args.count >= 3 ? Int32(args[2]) : nil
    let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as! [[String: Any]]
    for w in list {
        let pid = w[kCGWindowOwnerPID as String] as! Int32
        if let f = filter, f != pid { continue }
        if (w[kCGWindowLayer as String] as? Int ?? 0) != 0 { continue }
        let b = w[kCGWindowBounds as String] as! [String: CGFloat]
        let name = (w[kCGWindowName as String] as? String) ?? ""
        let owner = (w[kCGWindowOwnerName as String] as? String) ?? ""
        print("\(pid)\t\(w[kCGWindowNumber as String]!)\t\(owner) | \(name)\t\(Int(b["X"]!)) \(Int(b["Y"]!)) \(Int(b["Width"]!)) \(Int(b["Height"]!))")
    }
} else if args.count >= 3 && args[1] == "front", let pid = Int32(args[2]) {
    guard let app = NSRunningApplication(processIdentifier: pid) else { print("no such pid"); exit(1) }
    app.activate(options: [.activateIgnoringOtherApps, .activateAllWindows]); usleep(400_000); print("fronted \(pid)")
} else { print("usage: winctl windows [pid] | winctl front <pid>"); exit(2) }
