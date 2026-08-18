import Foundation

public struct OTADFUResult: Equatable {
    public var finalState: String
    public var started: Int
    public var transferCompleted: Int
    public var verified: Int
    public var activated: Int
    public var progressChunks: Int
}

public enum OTADFUSimulator {
    /**
     OTA/DFU 状态机回放：与 Python golden 同构。
     */
    public static func simulate(events: [String], targetChunks: Int = 8) -> OTADFUResult {
        var state = "idle"
        var started = 0
        var transferCompleted = 0
        var verified = 0
        var activated = 0
        var progress = 0

        for e in events {
            if e == "start", state == "idle" {
                state = "prepare"
                started = 1
                continue
            }

            if state == "prepare" || state == "transferring" {
                if e == "chunk_sent" || e == "ack_received" {
                    state = "transferring"
                    if e == "ack_received" { progress += 1 }
                    if progress >= targetChunks {
                        state = "verifying"
                        transferCompleted = 1
                    }
                    continue
                }
                if e == "disconnect" || e == "app_restart" {
                    state = "failed_recoverable"
                    continue
                }
            }

            if state == "verifying" {
                if e == "verify_ok" {
                    state = "activating"
                    verified = 1
                    continue
                }
                if e == "crc_error" {
                    state = "failed_recoverable"
                    continue
                }
            }

            if state == "activating" {
                if e == "activate_ok" {
                    state = "success"
                    activated = 1
                    continue
                }
                if e == "disconnect" {
                    state = "failed_recoverable"
                    continue
                }
            }

            if state == "failed_recoverable" {
                if e == "resume_with_token" {
                    state = "transferring"
                    continue
                }
                if e == "fatal_error" {
                    state = "failed_fatal"
                    continue
                }
            }

            if e == "fatal_error" {
                state = "failed_fatal"
            }
        }

        return OTADFUResult(
            finalState: state,
            started: started,
            transferCompleted: transferCompleted,
            verified: verified,
            activated: activated,
            progressChunks: progress
        )
    }
}
