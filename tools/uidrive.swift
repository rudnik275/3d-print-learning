// UIDrive — synthetic input for driving GUI apps (Bambu Studio) from a Claude session.
//   uidrive click <x> <y> [--double]      left click at screen coords (points, origin top-left)
//   uidrive move <x> <y>                  move pointer
//   uidrive type <text>                   type unicode text into the focused field
//   uidrive key <keycode> [cmd] [shift] [alt] [ctrl]   press a virtual keycode with modifiers (36=return, 53=esc, 48=tab)
//   uidrive scroll <x> <y> <dy>           scroll wheel at position (dy>0 = up)
// Needs Accessibility permission for UIDrive.app (System Settings → Privacy & Security → Accessibility).
import Foundation
import CoreGraphics
import AppKit
let a = CommandLine.arguments
func post(_ e: CGEvent?) { e?.post(tap: .cghidEventTap); usleep(60_000) }
func pt(_ x: String, _ y: String) -> CGPoint { CGPoint(x: Double(x) ?? 0, y: Double(y) ?? 0) }
guard a.count >= 2 else { print("usage: see source"); exit(2) }
if !AXIsProcessTrusted() { print("no accessibility permission for UIDrive.app"); exit(3) }
switch a[1] {
case "move":
    post(CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: pt(a[2], a[3]), mouseButton: .left))
case "click":
    let p = pt(a[2], a[3]); let dbl = a.contains("--double")
    post(CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: p, mouseButton: .left)); usleep(120_000)
    for i in 0..<(dbl ? 2 : 1) {
        let d = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: p, mouseButton: .left)
        let u = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: p, mouseButton: .left)
        d?.setIntegerValueField(.mouseEventClickState, value: Int64(i + 1)); u?.setIntegerValueField(.mouseEventClickState, value: Int64(i + 1))
        post(d); post(u)
    }
    print("clicked \(p.x),\(p.y)")
case "type":
    let text = a[2...].joined(separator: " ")
    for ch in text.utf16 {
        var c = ch
        let d = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: true); d?.keyboardSetUnicodeString(stringLength: 1, unicodeString: &c)
        let u = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: false); u?.keyboardSetUnicodeString(stringLength: 1, unicodeString: &c)
        post(d); post(u)
    }
    print("typed \(text.count) chars")
case "key":
    let code = CGKeyCode(UInt16(a[2]) ?? 36); var flags = CGEventFlags()
    if a.contains("cmd") { flags.insert(.maskCommand) }; if a.contains("shift") { flags.insert(.maskShift) }
    if a.contains("alt") { flags.insert(.maskAlternate) }; if a.contains("ctrl") { flags.insert(.maskControl) }
    let d = CGEvent(keyboardEventSource: nil, virtualKey: code, keyDown: true); d?.flags = flags
    let u = CGEvent(keyboardEventSource: nil, virtualKey: code, keyDown: false); u?.flags = flags
    post(d); post(u); print("key \(code) \(flags.rawValue)")
case "scroll":
    let p = pt(a[2], a[3]); let dy = Int32(a[4]) ?? 0
    post(CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: p, mouseButton: .left))
    post(CGEvent(scrollWheelEvent2Source: nil, units: .line, wheelCount: 1, wheel1: dy, wheel2: 0, wheel3: 0)); print("scrolled \(dy)")
default: print("unknown command"); exit(2)
}
