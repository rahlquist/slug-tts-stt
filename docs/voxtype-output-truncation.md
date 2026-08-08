# VoxType output truncation with remote STT

Date: 2026-08-08

## Symptom

Remote transcription completed correctly and VoxType notifications showed the full
transcript, but terminal and text-editor applications received only part of the
text—often the latter portion. Hermes itself received the complete transcript.

## Cause

The STT service and proxy were not truncating the transcript. The loss occurred
during VoxType's text-injection stage, using the `ydotool` output driver. VoxType
was configured with no inter-character delay:

```toml
[output]
type_delay_ms = 0
pre_type_delay_ms = 0
```

At zero delay, `ydotool` injected keystrokes faster than the receiving application
could consume them. Notifications were complete because they displayed the
transcript before output injection.

## Fix

Set a small typing delay in `~/.config/voxtype/config.toml` and restart the user
service:

```toml
[output]
type_delay_ms = 10
```

```bash
systemctl --user restart voxtype
```

After applying the 10 ms delay, the same dictation was delivered correctly to
plain terminal/text applications. No STT model, FLM/NPU service, or Hermes change
was required for this symptom.

## Diagnostic distinction

- Full text in the VoxType notification + partial text in the target app: output
  injection problem.
- Partial text in the notification itself: transcription/backend problem.
- `whisper-proxy.service` returns clean plain text for `response_format=text` and
  JSON only for `response_format=json`; its response format is independent of
  this keystroke-loss issue.

The delay value is a practical starting point; increase it if a particularly slow
application still drops characters.
