# Google Ads submit — current state (2026-09-13 evening)

## DONE (saved server-side, campaign 281499224402130)
- Search themes (9), 3 headlines (valid 30-char), long headline (78/90),
  2 descriptions (90), business name "Pocket Lota", $4/day budget, US geo
- Billing: account payment setup done by Arsal; payment iframe loads

## BLOCKER (last 5%)
3 images required: 1 landscape (1.91:1), 1 square (1:1), 1 logo (1:1).
The image-picker modal IS open on the Upload tab ("Upload from computer"
button visible). File-injection via CDP (DOM.setFileInputFiles on all 6
hidden inputs) is silently ignored by Google's uploader — it validates
trusted drop/click events.

## 2-MINUTE HUMAN FINISH
Files ready in C:\Users\Arsal\projects\pocket-lota-ad\pmax-assets\:
- landscape-1536x804.jpg
- square-1024.jpg
- logo-600.jpg
In the open modal: click "Upload from computer", select all 3, crop if
prompted, close modal. Then hit Submit (bottom-right, was enabled when
other fields were valid).

## Why not keep automating
Google's uploader rejects synthetic CDP file events (same class of problem
as Meta's AdsWorker video rejection). Playwright click-through also wedges
the SPA. A real gesture is the reliable path — same conclusion as the Meta
video upload saga.
