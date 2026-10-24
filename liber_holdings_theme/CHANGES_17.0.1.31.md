# Liber Holdings Theme 17.0.1.31

Brings the Liber site up to the standard already applied to the RBC Industrial
and Tooling Components themes, and closes the blog items Dale raised.

## What changed

| Area | Before | Now |
|---|---|---|
| Blog post header | The title repeated inside a large grey cover banner | The banner is gone and the title sits in a clean block above the article |
| Blog author bar | Author avatar, name and publication details shown on every post | Hidden, as agreed for a business readership |
| Grey placeholder thumbnails | A plain grey camera icon where a post had no picture | Carries the Technical Brief header, matching the sibling sites |
| Article content | A fixed width block, a wide table or a long unbroken line could push the page wider than the screen and shift the header | Content is contained: fixed widths shrink to fit, pictures scale, wide tables scroll inside their own box, and long text wraps. The page never scrolls sideways |
| Product and blog rows | Only the title text opened the item | Clicking anywhere on a row or card opens it. Links, buttons and form fields keep their own behaviour, Ctrl or Cmd click opens a new tab, and selecting text does nothing |
| Pager under the blog list | Sat tight against the last post | More space above it |
| Catalog pages in search | Listing pages competed with the transactional storefront | Listing pages under /shop carry a noindex tag on this website only. Product pages stay indexable, so brand visibility is kept |
| Reading the theme as a visitor | The homepage check could read the theme module directly, which public visitors have no permission to do | The read is done as superuser, so a visitor can never trigger a permission error on the homepage |

## Scope

Every style rule is scoped to `html[data-liber-theme]`, and the noindex rule
checks the website name, so RBC Industrial and Tooling Components are untouched
even though all sites share one database.

## Verified on a clean Odoo 17 database

* Module installs with no errors and reports version 17.0.1.31.
* Homepage, catalog, quote page and Contact Us all return 200 to a signed out
  visitor, with no permission error anywhere in the log.
* The noindex tag appears on /shop and does not appear on the homepage.
* The theme marker and the theme assets load on the page.
* The rule only fires for the Liber website: with another website name the
  catalog is left indexable.

## Still open from the meetings

* Add to Cart on Tooling Components: needs liber_holdings_theme 1.27 or later
  through the repository.
* Per brand descriptions: the field exists, the text is Dale's to supply.
* Spring values that differ by manufacturer: data, to agree with Dale.
* Bordignon image on H4025: upload from the shared drive.
* About page rework: waiting on Dale's mockup.
* Dale's SEO edits: merge his final PR before deploying this.


## Alignment with the sibling themes (added in this release)

RBC Industrial depends on `liber_holdings_theme`, so Liber is the base layer and
each sibling switches Liber's styling off on the website it owns. Thatcontract
only works if both sides name the same flag, and they did not.

| | Before | Now |
|---|---|---|
| The flag Liber looked for | `rbc_theme_active` | `x_rbc_theme_active`, which is the field RBC actually creates |
| Where the check lived | The same long expression repeated in six places across two files | One computed field, `website.is_liber_site` |
| Siblings recognised | RBC only, and only by a name that never matched | RBC and Tooling Components, through a list of flags that is easy to extend |
| Read permission | Some checks read the theme module, which public visitors cannot do | Computed as superuser, so a visitor can never trigger a permission error |

Because the old check never matched, Liber treated every website as its own and
only RBC's override layer kept its site clean. A website now belongs to Liber
when no sibling has claimed it, which is the rule the architecture always
intended.

# 17.0.1.32 (hotfix)

Version 1.31 broke /shop with `AttributeError: 'website' object has no attribute
'is_liber_site'`.

Cause. Apps > Import Module strips every Python file from the zip, so the
computed field never reached the database while the views that referenced it
did. The templates then asked for a field that did not exist, on every page.

Fix. No template depends on Python any more. The sibling check is written so
that it cannot fail either way:

    not (('x_rbc_theme_active' in website and website.x_rbc_theme_active)
      or ('x_tc_theme_active' in website and website.x_tc_theme_active)
      or ('x_tooling_theme_active' in website and website.x_tooling_theme_active))

A recordset answers `in` for a field name, so a missing field reads as absent
rather than raising. RBC creates `x_rbc_theme_active` from data XML, so it is
always present once RBC is installed, import or not.

The `is_liber_site` field stays for code to use on a repository deployment,
where Python does load. Nothing in the views needs it.

Verified by importing the zip exactly as the Apps screen does, with Python
stripped, on a clean Odoo 17 database:

| Check | Result |
|---|---|
| Module installs, reports 17.0.1.32, flagged as imported | yes |
| `is_liber_site` absent, which is the failing condition | confirmed absent |
| /shop | 200, with the noindex tag |
| Homepage and Contact Us | 200, no noindex |
| AttributeError anywhere in the page or the log | none |

# 17.0.1.33 and 17.0.1.34 (hotfix, product pages)

After 1.32 the catalog worked but every **product page** returned 500, on all
three websites, because `liber_holdings_theme` styles them all.

Two separate faults, both now fixed and verified.

**1. An unbalanced bracket (1.33).** While rewriting the sibling check in 1.31 a
closing bracket was lost, leaving `bool((website and not (...)))` one short.
QWeb could not compile the product template at all. Every expression in every
view file is now checked for balance, and the theme has none left.

**2. The template called Python that was not there (1.34).** The product page
runs `product._liber_product_json_ld(website)`. Apps > Import Module strips
Python, so that method does not exist on an imported install and the page
raised `AttributeError`. That block now also requires `'is_liber_site' in
website`, a field that only exists when the Python side is loaded. On a
repository deployment the structured data is emitted as before. On an imported
install it is skipped and the page renders.

Verified by importing the zip exactly as the Apps screen does, Python stripped,
on a clean Odoo 17 database:

| Page | Result |
|---|---|
| Product page | 200 |
| /shop | 200, noindex present |
| Homepage, Contact Us, /quote | 200 |
| Compile or render errors in the log | none |

## Worth knowing

This theme ships `models/`, `controllers/` and `hooks.py`, and an import drops
all of it. The cart gating, the quote controller and the menu rebuild hooks
therefore never run on an imported install. 1.34 makes the pages safe, not the
features complete: for the full behaviour the module has to go through the
repository, which is also what the task list says for 1.27.

# 17.0.1.35

The tile and card work done for RBC Industrial and Tooling Components, brought
across to the Liber catalogue, plus two faults seen on the live product pages.

| What was wrong | Now |
|---|---|
| Category tiles were different heights, because long names such as Motors and Controls or Press Die Components wrapped onto two lines | The picture box is a fixed square, so a letter placeholder takes the same room as a photograph, labels hold two lines, and every tile in the row is the same height |
| Product cards ended at different heights, so the quote buttons did not line up | Cards share a height, the picture box has a floor, and the description keeps its height whether a product has one or not |
| SKU and Direct Quote collided, with Direct Quote breaking across two lines | They share a row, the note stays on one line and a long SKU wraps instead of pushing the card wider |
| Specification badges could stretch a card | They wrap inside it |
| Every single-value attribute was listed twice: once in the theme's Technical Specifications table and again underneath in Odoo's own block | Odoo's repeat is hidden and the theme's table is the only one |
| The product page advertised a 30 day money back guarantee and 2 to 3 day shipping, on a catalogue that sells through quotes | Hidden on this website. The share buttons beside it stay |

All of it is style only, scoped to `html[data-liber-theme]`, appended at the end
of theme.css. No markup, data or behaviour changed, and the sibling sites are
untouched.

Verified by importing the zip as the Apps screen does, Python stripped, on a
clean Odoo 17 database: product page, catalog, homepage and Contact Us all 200,
the new rules present in the served stylesheet, no render errors.

## Not a theme problem: "This product has no valid combination"

That message is Odoo's own, shown when the configurator cannot resolve a
variant for the product at all. It is the duplicate variant fault: the stocked
variant carries values the configurator does not ask for, so nothing matches.
It also explains why Brand reads "Raymond, Bordignon Springs" on one line,
since with no variant resolved the table falls back to listing every value.

Fix it with the variant tools, not here: run Repair All Variants on that
product, then reload the page.

# 17.0.1.36

| Seen on the live site | Now |
|---|---|
| "View-Only Catalog" badge on the product page | Hidden. The element stays in the markup so the sibling themes' xpaths over this template keep matching |
| SKU and Direct Quote still collided, with Direct Quote on two lines | Firmer rule: the row never wraps, the note stays on one line, and a long SKU is cut with an ellipsis instead of pushing the card about |
| The sidebar filters were a plain radio list, nothing like the compact filter card on the sibling sites | Filters sit in a bordered card that follows you down the page, with small uppercase headings in the Liber red, one tidy column of options aligned on their controls, expand arrows on the right and indented sub-categories |
| Cards and tiles were flat | A restrained lift and shadow on hover, the same gesture the sibling sites use, and switched off for anyone who asks for reduced motion |

Style only, scoped to `html[data-liber-theme]`, except the one markup change that
adds a class to the badge. The sibling sites are untouched.

Verified by importing as the Apps screen does, Python stripped: product page,
catalog, homepage and Contact Us all 200, every new rule present in the served
stylesheet, the 1.36 SKU rule correctly overriding the 1.35 one, no render
errors.

# 17.0.1.37 and 17.0.1.38

## Appearance

| | |
|---|---|
| Product cards | A signal-red line draws itself across the top on hover, the card lifts, and the photograph zooms slowly inside its frame |
| Category tiles | A soft white to grey wash, and a letter placeholder is now a dark monogram panel rather than bare text |
| Buttons | A deeper red gradient with a shadow that grows as the button lifts, and settles when pressed |
| Filters | A frosted card with a light blur that follows you down the page, options highlighting on hover |
| Headings | A short red accent rule beneath each one |
| Specification table | Alternating row tint and a highlight on the row under the cursor |
| Panels | Fade up gently as they come into view, capped at sixty per page so long catalogues stay quick |

Everything respects a reduced-motion preference: all of it stops, nothing moves,
and the content shows immediately.

## Menu order and page alignment

Home was second in the menu, behind Contact us, which is also why the bare
domain fell through to the Contact page. On install, and on every upgrade, the
theme now:

* puts the menus in order: Home, Shop, Brands, Technical Resources, About, Contact
* creates a Home entry if one is missing but a published home page exists
* removes duplicate Home entries
* points the website's homepage URL at the home page, but only when that page
  exists and is published

It is written as a data action rather than Python, so it also runs when the
module is installed through Apps > Import Module. There is a menu entry,
**Website > Configuration > Liber: fix menu order**, to run it again after any
deployment that disturbs the menus.

Pages also share one grid now: the same container width, the same vertical
rhythm between sections, and the same left edge for headings and body text.

## Verified

Imported exactly as the Apps screen does, Python stripped, on a clean Odoo 17
database carrying the live fault (Contact us first, Home second, duplicate Home
entry, no homepage URL):

| Check | Result |
|---|---|
| Menu before | Contact us > Home > Shop > Brands > Home > Blog |
| Menu after | Home > Shop > Brands > Blog > Contact us |
| Duplicate Home entry | removed |
| Homepage URL | set to /home |
| Root, /home, /shop, /contactus, product page | all 200 |
| New style rules in the served stylesheet | present |
| Render errors | none |

One gap: the theme's JavaScript is registered as an asset, and I confirmed the
record exists, but my test server stopped responding before I could confirm the
reveal script reaches the served bundle. The styling does not depend on it. If
panels do not fade in, the cause is there and nothing else breaks.

# 17.0.1.39

## The duplicate specification list is gone for good

1.35 hid it with a style rule. That was not enough, so the block is now switched
off in the template itself, on this website only: Odoo's
`#product_attributes_simple` no longer renders at all. Confirmed by reading the
rendered page, where the block is absent rather than merely invisible.

## Clicking anywhere on a card opens the product

Previously only the picture and the title were links, and the clickable row
added in 1.31 depended on the theme's script, which may not reach the page on an
imported install. The whole card is now a link in CSS alone, so it works
regardless. The Request Quote button and the SKU stay above that overlay and
keep their own behaviour.

## A Family of Companies

| Before | Now |
|---|---|
| Five plain white boxes, logos at different sizes, nothing happening on hover | Each logo sits in a fixed box so all five line up whatever their shape |
| | Logos are muted and come to full colour as you hover |
| | A red rule wipes down the left edge, the card lifts, the border picks up the brand colour |
| | Cards share a height, and stack to a centred column on a phone |

Verified on a clean Odoo 17 database with the module imported as the Apps screen
does: product page, homepage, catalog and Contact Us all 200, the duplicate
block absent from the rendered HTML, no render errors.

# 17.0.1.40

| What you reported | What changed |
|---|---|
| Hero buttons almost invisible, dark on a dark hero | Three distinct weights: a solid white primary, a bordered glass secondary and a red gradient accent. Each lifts on hover |
| Hero text hard to read against the background | A gradient veil sits behind the words, with a slight shadow on the text, so it reads over any image |
| SKU badge and Direct Quote collided | They can no longer touch: the badge is capped at about two thirds of the row and cut with an ellipsis, the note is pushed to the far edge and never wraps |
| Clicking inside the box only worked on the picture or the title | The whole card opens the product, in grid and in list view. The quote button, the wishlist heart and the SKU stay clickable on top |

Verified on a clean Odoo 17 database with the module imported as the Apps screen
does: homepage, catalog, Contact Us and the product page all 200, every new rule
present in the served stylesheet, no render errors.

# 17.0.1.41

| What you reported | What changed |
|---|---|
| Company cards had no links, or the wrong ones | Each subsidiary name and its button now open that company's own site: rbc-industrial.com, toolingcomponent.com, globeelectricsupply.com, liberindustrial.com. They open in a new tab |
| Footer subsidiary names were plain text | The four names are links to the same sites |
| Timeline entries looked different from one another | One pattern throughout: the same red top rule, the same border and shadow, markers the same size, shape and colour, and year badges that match. Cards lift on hover |
| Contact Us and Contact both in the menu | The menu action now removes the duplicate, as it already did for Home |
| No picture zoom on products, unlike the sibling sites | Zoom on hover turned on, click to magnify left off, which is how RBC and Tooling are set |
| Telephone numbers and email addresses were not clickable | Any tel, mailto or map link now reads as a link and picks up the brand colour on hover. Where a number is still plain text in the page content, it is content rather than theme: edit it in the page and Odoo will link it |
| The hero was a flat dark slab | Layered: two soft brand-coloured washes, a faint engineering grid that fades at the edges, a pill-shaped badge, a headline that scales with the window and carries a red rule beneath it |
| The figures bar was plain centred text | Large red figures, small uppercase labels, each column lighting up as you pass over it |

Verified on a clean Odoo 17 database with the module imported as the Apps screen
does: homepage, catalog, Contact Us and product page all 200, the zoom views set
correctly in the database, every new rule present in the served stylesheet, no
render errors.

## What I could not do from here

The timeline and contact rules are written against the structure in these
templates. Where those blocks were built in the website editor instead, they
carry different markup and the rules will not reach them. If an entry still
looks different after importing, it was edited on the page and needs editing
there.

# 17.0.1.42 — why nothing appeared to change

Everything from 1.35 to 1.41 was in the zip, but on an imported install none of
it reached the browser.

The theme already clears Odoo's cached stylesheet in `hooks.py`, so that the
browser is served a freshly built one. Apps > Import Module strips every Python
file, `hooks.py` with them, so that step never ran. Odoo kept serving the
stylesheet built before any of these changes existed, and the site looked
untouched no matter how many versions were imported.

The same step is now a data action, which an import does run. It is the last
data file in the module, so it runs after everything else, on install and on
every upgrade.

| Check on a clean Odoo 17 database, imported as the Apps screen does | Result |
|---|---|
| Cached stylesheet files before the import | 2 |
| Cached stylesheet files after the import | 0, cleared and rebuilt on the next page load |
| Homepage | 200, with the theme flag on the page |
| Hero button rules in the served stylesheet | present |
| Figures bar rules | present |
| Timeline marker rules | present |
| Subsidiary link rules | present |
| Duplicate specification block | switched off |
| Render errors | none |

There is also a menu entry, **Website > Configuration > Liber: rebuild
stylesheet**, for use after any change that leaves the site looking stale.

After importing, reload the website with Ctrl+Shift+R. The browser caches the
stylesheet by its address, and the address only changes once Odoo has rebuilt it.

# 17.0.1.43

**Clicking anywhere on a card.** Earlier attempts stretched one of Odoo's own
links across the card, which depended on markup that differs between the grid
and the list. Each card now carries its own full-size link to the product, added
in the template, so it behaves the same in both views and needs no JavaScript.
Verified in the rendered page: the anchor is present in grid and in list, and
its address is the product's own. The quote button, the wishlist heart and the
SKU sit above it and keep their own behaviour.

**Hero buttons.** Now also addressed by their destination, not only their class,
with visibility, opacity and stacking forced. Our Companies is solid white,
Brands We Represent is bordered glass, Request a Quote is the red gradient.

**The history page.** Every entry is forced to one format: the same title size
and weight, the same body colour and size, the same card frame and red top rule,
year labels that match, and markers reduced to one neutral white dot on a red
circle, which removes the assorted lightning bolts and letters.

## Something you should know about this page

The About page, including the history tree, is written by `models/website.py`.
Apps > Import Module strips Python, so that code has never run on your site: the
page you see is content stored in the database from an earlier deployment or
from editing in place. These rules reach it by structure, so they should apply,
but anything genuinely inconsistent in the stored content can only be corrected
on the page itself or by deploying the module through the repository.

The same is true of the homepage template, which is why I could not render the
hero in my own test database: the theme's homepage only becomes the live page
when the Python side runs.

# 17.0.1.44 — the three stubborn items moved out of the stylesheet

Each of these was fixed in an earlier version and each kept coming back. The
common thread is the stylesheet: it is cached by address, and until Odoo
rebuilds it the browser keeps the old one, so a style-only fix can sit in the
database doing nothing.

These three now carry their styling **in the page itself**, which is sent fresh
on every request and cannot be cached away:

| Item | How it is fixed now |
|---|---|
| SKU and Direct Quote running together | Both carry inline styles: the row cannot wrap, the badge is capped and cut with an ellipsis, the note is pushed to the far edge |
| The product block not clickable | The overlay link carries its own inline position and size, so it covers the card whatever the stylesheet says. The quote button is raised above it inline |
| Hero buttons invisible | All three carry their own inline background, text colour, border and stacking |

Confirmed by reading the served HTML, not the stylesheet:

    <a class="o_liber_card_overlay" style="position: absolute; top: 0; right: 0;
       bottom: 0; left: 0; z-index: 1; ..." href="/shop/..."

The SKU row and the Direct Quote note show their inline styles in the same way.

This is deliberately heavier handed than good practice would suggest. It is the
right trade while the site is being updated by import rather than through the
repository, because it removes the stylesheet from the equation entirely.

# 17.0.1.45 — the history timeline rebuilt from inside the module

Styling could not fix this one. The entries were written into the page at
different heading levels with four different marker glyphs, and the markers sat
beside the spine rather than on it. No stylesheet can turn an h5 back into an h3
or move a marker that is in the wrong column.

So the module now rewrites that part of the page itself, as a data action, which
an import does run.

**What it does.** It finds the About page, locates the timeline by its own text,
replaces that one section with a single consistent block, and leaves the rest of
the page alone. Running it again does nothing, because it recognises its own
work.

**The new structure.** Three columns: card, spine, card. Entries alternate
sides. Each has the same heading level, the same body text size and colour, the
same card frame with a red top rule, one red dot on the spine and a year label
beneath it. On a phone the spine moves to the left and the cards line up beside
it.

**Six entries**, in order: 1987 Roger Brown Co founded, 2016 acquisition, 2018
Liber Industrial, 2023 Tooling Components, 2024 Globe Electric, 2025 RBC
Industrial rebrand. The 1987 entry is new; the live page started at 2016.

## Verified against a page built like yours

A test page was given mismatched headings (an h3 and an h5), a lightning bolt
and a dollar marker, and some unrelated content below.

| Check | Result |
|---|---|
| Rebuilt section present after import | yes |
| Entries | 6, every title at the same level |
| Mismatched icons left | 0 |
| Unrelated page content below the timeline | survived |
| /about-us renders | 200 |
| Dots, years and rows in the page | 6 of each, 1987 through 2025 |
| Timeline styles in the served stylesheet | present |
| Render errors | none |

There is a menu entry as well, **Website > Configuration > Liber: rebuild
history timeline**, for running it again after any change.

**Worth knowing.** This overwrites that section of the page, so if Dale has
edited the timeline text in the editor, his wording there is replaced by the
wording above. The text came from your own screenshots. Tell me of any
correction and I will put it in the module.

# 17.0.1.46 — the company links corrected where they actually live

The "A Family of Companies" block on the live site is page content, not the
module's own template, which is why the links added to the template in 1.41
never appeared there. It is corrected in the page itself now, as a data action.

| Company | Opens |
|---|---|
| RBC Industrial | rbc-industrial.com |
| Tooling Components | toolingcomponent.com |
| Liber Industrial | liberindustrial.com |
| Roger Brown Co | rogerbrownco.com |
| Liber Land | /contactus |

The external ones open in a new tab. A name already linked to the right address
is left alone, so the action is safe to run again, and there is a menu entry,
**Website > Configuration > Liber: fix company links**.

Verified on a page built like yours, where four names were plain text and one
was wrapped in a wrong link: all five point at the right address afterwards.

**Liber Land** is the one I could not source. The other four domains come from
the addresses on your contact page. It points at the contact page for now. Send
me its address and I will put it in.

# 17.0.1.47 — the company links, properly this time

1.46 did not work and here is why: it looked for the company name wrapped
tightly in its tag, as `>RBC Industrial<`. On your page the names sit on their
own lines inside the tag, so nothing matched and nothing was changed.

Matching now ignores whitespace and line breaks around the name and is not case
sensitive. Tested against markup written the way yours is, with names on
separate lines, inside spans, headings and bold tags, and one already wrapped in
a wrong link. All five were linked correctly.

## The addresses are editable now

Six fields were added to the website record, so these are no longer fixed in the
module:

| Company | Field | Default |
|---|---|---|
| RBC Industrial | x_liber_url_rbc | rbc-industrial.com |
| Tooling Components | x_liber_url_tc | toolingcomponent.com |
| Liber Industrial | x_liber_url_li | liberindustrial.com |
| Roger Brown Co | x_liber_url_rb | rogerbrownco.com |
| Liber Land | x_liber_url_ll | /contactus |
| Globe Electric Supply | x_liber_url_ge | globeelectricsupply.com |

To change one: Settings > Technical > Database Structure is not needed. Open
Website > Configuration > Settings in developer mode and edit the field, or set
it on the website record, then run **Website > Configuration > Liber: fix
company links**. The new address is applied to the page.

External addresses open in a new tab; an internal one such as /contactus opens
in the same tab. A name already pointing at the right address is left alone.
