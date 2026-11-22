# Rating study a4-v2: runbook

From "the final run has finished" to "the ratings are analysed". The plan and its reasons are in
[`FINAL_CALL.md`](FINAL_CALL.md). Nothing below makes a paid call except the optional step 4.

Two checkouts are used. `MB` is MolBench (branch `final-benchmark` with `fb/rating2` merged);
`CD` is molstar-chat-driver (branch `feat/rating-v2` merged to `main`).

    MB=/home/danbolser/Build/MolBench
    CD=/home/danbolser/Build/molstar-chat-driver
    RUN=$MB/results/final-v1             # the finished run: it holds samples/spec/<model>.jsonl
    A4=$MB/results/a4/a4-v2              # private: results/ is git-ignored

**Never** commit, print or paste `$A4/key.json`, `$A4/seed_rating_items.sql`, `$A4/review/`,
`$A4/raters.json`, an invite token or a rater's name. The builder refuses a key path that git
would pick up.

## 0. Before the run finishes (once)

    cd $MB
    uv sync --extra execute --extra authoring --group paper
    uv run python scripts/fetch_molstar.py          # the pinned Mol* bundle
    uv run playwright install chromium              # the headless browser
    uv run pytest -q tests/test_rating_set.py tests/test_agreement.py

Pictures are drawn by headless Chromium with software GL (SwiftShader). No GPU and no display
are needed; it worked on this machine (112 cores, no GPU). It is slow: about 16 seconds per
picture, four pictures per pair.

Decide and write down (in `FINAL_CALL.md`) before the first rating: the reading rule for the
paper, and what to do about doubled drawings (open issue 1 below).

## 1. See what the run offers (seconds, draws nothing)

    cd $MB
    uv run python scripts/build_rating_set.py $RUN --set a4-v2 --plan-only

Prints the valid scenes per tier and grader verdict (right / close / wrong), what is left out
and why, and a sample drawn with a throwaway key. Check: every tier has pairs in every verdict
it can; "close" is not empty.

## 2. Build the set

    uv run python scripts/build_rating_set.py $RUN --set a4-v2 \
        --out $CD/site/rate/a4-v2 --key $A4/key.json --jobs 16

- Writes the public items (`items.json`, `img/`: ids, requests, pictures, nothing else) into the
  site, and the private key, `seed_rating_items.sql` and `review/` next to the key.
- Time: about 6 minutes for 24 items with 4 jobs on this machine; plan one to two hours for the
  full set with 16 jobs. Every picture is cached under `$A4/render_cache`, so a second start
  draws only what is missing, and the same key gives the same ids.
- Answers that load a structure from the internet are fetched while drawing. `--offline` refuses
  that; such answers then cannot be drawn and are replaced, which removes wrong-structure
  answers from the "wrong" class. Leave it online unless there is a reason.
- Back the key up at once: `cp -a $A4/key.json ~/Backups/a4-v2-key.json`.

**Read the last lines it prints.**

1. `passes drawn: N, of which M look different from the reference`. If M is under a quarter of
   N, most "right" pairs are identical pictures and test nothing. Then rebuild with fewer of
   them, e.g. `--mix 1:2:2` (right : close : wrong), and say in the paper that the study bounds
   false fails, and false passes only on M-like answers. Dan's call.
2. `answers that could not be drawn (replaced)` and `checks rejected` should be small; the key
   lists each under `sample`.

## 3. Look before anyone else does

    ls $A4/review/                 # one sheet per item: reference | answer, whole above zoomed
    column -t -s$'\t' $A4/review/index.tsv | less -S

Open at least: every `close` sheet, 20 `clinical` sheets, every check. Look for:

- a "close" answer whose zoomed picture shows no highlight at all (open issue 1);
- zoomed views where the target is hidden or cut;
- checks whose known answer is not obvious.

Then rehearse the page on this machine, with nothing deployed and no database:

    cd $CD && npm ci && npm run build:site
    npx tsx test/rate-local.mts --set a4-v2 --items site/rate/a4-v2 --seed $A4/seed_rating_items.sql
    # open http://<this-host>:8791/rate.html?e=anything   (the server listens on 127.0.0.1: use an ssh tunnel)

Rate 35 items yourself and time it. `http://127.0.0.1:8791/log` shows what was stored.

## 4. Optional: the image-pair judge (paid; Dan's go)

Not built: there is no runner that puts the four v2 pictures of a pair to the judge. If it is
wanted, it must judge the pictures in `$CD/site/rate/a4-v2/img/` and write one JSON object per
line: `{"model": ..., "task_id": ..., "sample": ..., "label": "same"|"different", "score": ..., "judge": ...}`
(model, task and sample of each pair are in the key). Then rebuild with the verdicts; nothing is
redrawn and no id changes:

    cd $MB && uv run python scripts/build_rating_set.py $RUN --set a4-v2 \
        --out $CD/site/rate/a4-v2 --key $A4/key.json --judge $A4/judge.jsonl

Skip this and the analysis says "the image-pair judge was not run on these pairs".

## 5. Freeze the analysis

    cd $MB && git add paper/a4/FINAL_CALL.md && git commit -m "Rating study a4-v2: plan fixed before the first rating"
    git tag a4-v2-analysis          # scripts/agreement.py at this commit is the analysis

## 6. Put it online (in this order)

1. **Database.** In the Supabase SQL editor of the rating project, run the block of
   `$CD/supabase/schema.sql` from the line `Rating study a4-v2 (MIGRATION)` to the end. It only
   adds: a column `ratings.target_label`, tables `rating_items` and `rating_repeats`, a function
   `rating_counts`. a4-v1 rows are untouched. (The project pauses when idle; restore it first.)
2. **Serving plan.** In the same editor, run `$A4/seed_rating_items.sql` (private: paste it,
   do not commit it).
3. **Whose answers do not count towards a pair's two raters:** the author's and any testing token.

       cd $CD && supabase secrets set RATE_IGNORE_TOKENS=<author token>,<test token>

4. **Function.** `supabase functions deploy rate`
5. **Pictures and page.** Commit `site/rate/a4-v2/` (about 60 MB of JPEGs for 330 items) and
   merge to `main`; the Pages workflow publishes it. From then on `rate.html` opens a4-v2 by
   default and `rate.html?set=a4-v1` still opens the pilot.
6. **Check live** with a testing token: `https://dbolser.github.io/molstar-chat-driver/rate.html?e=<test token>`.
   Answer three items; confirm rows in `ratings` with `set_id = 'a4-v2'` and a `target_label`.
   Do this only after step 3, or the test answers use up second-rater places.

If step 5 goes out before steps 1, 2 and 4, the page shows a4-v2 but nothing is served. Keep
the order.

## 7. Invite

    cd $CD
    export SUPABASE_URL=https://<project-ref>.supabase.co SUPABASE_SERVICE_ROLE_KEY=<service-role key>
    export SITE_URL=https://dbolser.github.io/molstar-chat-driver
    npm run mint:invites -- "<name>" "<name>"        # prints one private link per person

The printed links open the chat; the rating link is the same token on `rate.html`:
`https://dbolser.github.io/molstar-chat-driver/rate.html?e=<token>`. Send the message in
`FINAL_CALL.md` ("Draft message to volunteer raters") with each person's link, the draft-paper
link and the closing date filled in. Aim for 20 people.

## 8. While it runs

    cd $MB
    uv run python scripts/export_ratings.py --set a4-v2 --author "<author's token name>" --test "<test token name>"
    uv run python scripts/agreement.py $A4/key.json $A4/ratings.json --reps 200 \
        --json /tmp/a4-v2-progress.json --markdown /tmp/a4-v2-progress.md

The export sends SELECTs only. Watch: raters finished, pairs with two labelled answers, anyone
failing the checks. Do not read the agreement numbers as results until the study closes.

## 9. Close and analyse

    cd $MB && git checkout a4-v2-analysis -- scripts/agreement.py      # the frozen analysis
    uv run python scripts/export_ratings.py --set a4-v2 --author "<author's token name>" --test "<test token name>"
    uv run python scripts/agreement.py $A4/key.json $A4/ratings.json \
        --json paper/a4/tables/agreement_v2.json --markdown paper/a4/tables/agreement_v2.md
    cp -a $A4 ~/Backups/a4-v2-$(date +%F)

`agreement_v2.md` holds, in order: the data; raters and checks; **task success against people
(whole scene)**; **target score against people (zoomed view)**; what people said by the grader's
verdict, with the passes whose pictures differ shown apart; by tier; people against people and
test-retest; the image-pair judge if it was run; flags and notes. Each table has three columns:
independent raters who pass the checks (primary), without the author, all raters.

The two generated files carry pseudonyms, task ids and raters' notes. Read the notes before
committing them. Giving the script a v1 key with v2 ratings, or the reverse, is refused.

## Open issues for the lead

1. **Doubled drawings.** An answer that draws the chain grey and then the target again, in
   colour, in the same place, gets target score 1; this renderer shows the grey only. Both
   "close" answers of the pilot run are like this. Not checked: what a GPU shows (probably
   flicker between the two). Choices: (a) leave it, and let the study report that people call
   these different; (b) have the grader's target score require the target's colour to be the
   only one drawn on those atoms; (c) draw later representations on top. (b) and (c) touch
   `molbench/drawn.py` / `molbench/render.py`, which this job does not own.
2. **Identical passes.** All 14 passes of the pilot run are pixel-identical to the reference.
   See step 2.
3. **No judge runner for v2 pictures** (step 4).
4. **`site/SETUP.md` §10** in molstar-chat-driver still describes the a4-v1 serving and an
   `agreement.py --from-supabase` that does not exist; not edited here.
5. **Time per sitting is a guess** (step 3 measures it). If 35 items take much over 15 minutes,
   lower `GOAL` in `supabase/functions/rate/plan.ts` and `PER_RATER` in the builder together.
6. **Two raters at the same moment** can both be given the same unopened pair (good), and three
   can too (a third answer). Harmless at this scale; not prevented.
