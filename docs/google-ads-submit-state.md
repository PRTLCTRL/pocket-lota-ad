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

## 2026-09-18 agent verification (backlog worker, no browser touched)
- [x] All 3 asset files confirmed on disk at exact spec: landscape-1536x804.jpg
  (1536x804), square-1024.jpg (1024x1024), logo-600.jpg (600x600) - logo is
  Lota Lemon (pixel-avg identical to public/lota-lemon.png crop).
- [x] Organic Short still live and counting: unP_KclQgn8 on Arxa channel
  (YouTube feed + watch page HTTP 200; viewCount 113, 0 likes as of Sep 18) -
  video asset for the campaign is healthy.
- [x] Destination Worker still up: pocket-lota-ad.prtl.workers.dev returns HTTP 200.
- Nothing else changed; the 2-minute human finish above is still the only
  remaining step before Submit. Session age warning: if the modal/tab was
  closed since Sep 13, re-open the campaign and just do the upload+submit.
