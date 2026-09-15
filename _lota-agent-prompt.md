Improve the Pocket Lota store landing page AND deploy it as a Cloudflare Worker.

This is a local checkout of PRTLCTRL/pocket-lota-ad. Do the work in this cwd. Do not clone. Do not use Cursor cloud VMs.

Page:
- Apple / Gen Z product page. Huge type, quiet space, one idea per scroll. Dark, yellow accent.
- Hero: quiet product loop if present (lota-hero-loop.mp4 / apple loop), NOT the hallway infomercial.
- $19.99 USD. Sticky Buy to https://pocketlota.com until Stripe.
- Female Lota Lemon in the header if lota-lemon.png exists.
- Copy you may use: It just pours. / Wipe culture is over. / Your other daily driver. / Think different. Stay cleaner.
- No fake reviews or star ratings.

Deploy:
- wrangler.jsonc should serve static assets (public/ or equivalent).
- Run wrangler deploy (account is already authenticated).
- Name: pocket-lota-ad. Print the live workers.dev URL. That URL is done.

Do not invent reviews. Do not spend money. Do not touch Keel.
