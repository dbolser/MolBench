# Release checklist: from here to submission

State on 2026-11-23, branch `final-benchmark`: corpus, graders, runner, paper draft and rating
tooling are built and checked at no cost. Nothing is frozen: no tag, no pinned hash, no paid
run. The steps below are in order; each has its command. Run them from the repository root
(`/home/danbolser/Build/MolBench`) unless a step says otherwise.

Rules that hold throughout: never pass `--no-archive`; never print or commit a key, `.env`,
`results/a4/**/key.json` or a rater's name; never edit a generated task file by hand (change
the generator and regenerate); after the freeze, no task, prompt or grader rule changes
without a new corpus version.

## 0. Decide first (Dan)

Each of these changes what the run measures or costs, so it is settled before the freeze.

| # | Decision | Default if nothing is said | Where it is described |
|---|---|---|---|
| a | An upper-case PDB id on the call-list track scores 0 (it loads nothing in pdbe-molstar 3.3.2) | stays as built: scores 0, and the format guide says so | `PILOT.md`, "For the lead to rule on" |
| b | Token limit for models with hidden reasoning (16,000 now; one pilot model spent 10 hidden tokens per visible one and hit the limit in 12 calls) | stays 16,000; truncated answers are counted apart | `run/final_run.toml`, `[run]` |
| c | Run size: lean ($63), recommended ($138), or with optional frontier models (up to $496) | recommended, no optional model | `run/README.md`, "Run sizes" |
| d | Reading rule for the rating study (90% confirmed, lower bound 0.80) | must be confirmed before the first rating, not before the run | `paper/a4/FINAL_CALL.md` |
| e | Merge `final-benchmark` into `main` before or after the preprint | after the run, by pull request | – |

## 1. Freeze the corpus

```bash
git switch final-benchmark && git pull
uv sync --extra execute --extra authoring --extra anthropic --extra openai --group paper
uv run python scripts/fetch_molstar.py && uv run playwright install chromium
uv run pytest -q                                          # must pass
uv run python scripts/validate_tasks.py --final           # OK: 879 tasks
uv run python scripts/grader_controls.py --check          # 0 false passes, 0 false fails
python -m molbench.manifest run/final_run.toml            # prints "sha256 on disk <hash>"
```

Then, in `run/final_run.toml`, section `[corpus]`: set `version = "corpus-v1.0"` and
`sha256 = "<hash>"`. In `paper/sections/12_availability.md` and `paper/si/s6_run.md`, replace
the two `⟦PENDING: corpus freeze …⟧` tags with `` `{{plan.corpus_sha256}}` ``.

```bash
python -m molbench.manifest run/final_run.toml            # now says the hash is pinned and matches
uv run python paper/corpus_values.py && python paper/build.py
uv run pytest -q
git commit -am "Freeze corpus-v1.0: version and hash pinned"
git tag -a corpus-v1.0 -m "MolBench corpus v1.0: 879 task files, sha256 <hash>"
git push origin final-benchmark corpus-v1.0
```

The hash on 2026-11-23 is `45a841aecbd25a72c0d1f9a91704b3031318955bd44300e3bf547ffa95e4edd8`.
It changes if any file under `tasks/` changes.

## 2. Top up, and key hygiene

The run uses two routes: OpenRouter for 20 of the panel's models, and the Anthropic API for
claude-haiku-4-5. The two scripted baselines call nothing.

1. **OpenRouter.** Make a new key used by MolBench only, with a credit limit equal to the
   budget cap ($165 for the recommended run). Limits are per key but the balance is per
   account: another project emptied this account in November 2026, so cap or remove that
   project's key before adding credit. Do not use the chat site's key.
2. **Anthropic.** Check the balance covers the model's share (the plan command below prints
   the cost per model).
3. Put both keys in `.env` at the repository root (`OPENROUTER_API_KEY=…`,
   `ANTHROPIC_API_KEY=…`). `.env` is git-ignored; `git status` must not show it.
4. Check the prices are still current: the manifest's were read on the date in each
   `price = { … date = … }` entry. If a price moved, change it in the manifest with its date.

```bash
git status --short .env                                   # prints nothing
python -m molbench.runner --manifest run/final_run.toml   # plan and projected cost per model; no call is made
```

The projected total must be under `budget.cap_usd`; a test holds the cap between the
projection and 1.5 times it.

## 3. Rehearse (no cost)

```bash
python -m molbench.runner --manifest run/final_run.toml --dry-run
```

Expect `DRY RUN PASSED` with 23 of 23 checks. On 2026-11-23: 91,647 cells with the optional
models; 71,982 calls for the core panel.

## 4. The one run (paid)

```bash
mkdir -p runs && nohup python -m molbench.runner --manifest run/final_run.toml --go \
    > runs/final-v1.log 2>&1 &
tail -f runs/final-v1.log
```

- **Expected cost:** $138 for the recommended run (cap $165). The provider pilot came in 7%
  under its projection on the one priced route. The run stops itself when spent plus
  still-to-run passes the cap.
- **Expected time:** not measured. From the pilot's latencies (about 2 s per call on the
  fastest route, about 26 s for a model that reasons) and 8 calls in flight, 65,874 provider
  calls take somewhere between one and two days. Leave it running in `nohup` or `tmux`.
- **To resume** after a stop, a crash or the cap: start the same command again. Every
  archived call is kept and skipped; calls that failed every retry are listed in
  `runs/final-v1/errors.jsonl` and are tried again. A second start while the first is still
  running is refused by a file lock, which goes away with the process.
- **One model at a time**, or a model added later: `--only-models <id> [<id> …]`. Optional
  frontier models: `--include-optional`, after raising the cap (`run/README.md`).
- **Afterwards:** `runs/final-v1/errors.jsonl` should be empty or explained. Re-grading never
  costs anything: `python -m molbench.runner --manifest run/final_run.toml --grade-only`.
- **Back up at once:** `cp -a runs/final-v1 results/final-v1 ~/Backups/molbench-final-v1-$(date +%F)/`,
  and one copy off this machine.

## 5. Tables and the paper

```bash
python scripts/paper_tables.py --from-run results/final-v1 --into-paper
uv run python paper/corpus_values.py
uv run --with matplotlib python paper/figures.py
python paper/build.py --pdf
cat paper/PENDING.md
```

`--into-paper` writes the seven `table_final_*.md` files that the paper includes and
`paper/generated/final_values.json`; it refuses a dry run, a pilot and an incomplete run. That
fills 182 of the pending cells. What then remains is prose, and `paper/PENDING.md` lists each
place:

- the result sentences (abstract, introduction, Sections 6.1 to 6.5, discussion, conclusion):
  write them with `{{final.<key>}}` values, never typed numbers; the key names are those of
  `paper/generated_mock/values.json`;
- the further tables of SI Section S9, from `paper/generated_final/`;
- the abstract must stay within 200 words: the two result sentences replace the four on the
  pilot run;
- author decisions (authors, acknowledgements, consent wording, table-of-contents graphic).

**Not built yet:** the three panels of the result figure (Figure 5) have a layout
(`fig_result_shapes.svg`) but no script that draws them from a run. This is work at no cost
and can be done before the run, against `results/final-v1.dryrun`.

Then publish the leaderboard from the same scorecards (`results/final-v1/site/`), and re-sync
the chat driver's vendored reference (`node scripts/sync-prompt.mjs <MolBench>` in
molstar-chat-driver).

## 6. Clarity review of the filled paper

One more round with the five reviewers of `paper/REVIEW_LOG.md` on the paper with results in
it; the last round on the empty-table draft gave 8 of 10 from every reviewer. Somebody reads
both PDFs end to end.

## 7. Second rating study (a4-v2)

The commands, in order, are in [`paper/a4/RATING_V2_RUNBOOK.md`](paper/a4/RATING_V2_RUNBOOK.md).
In outline:

```bash
RUN=results/final-v1; A4=results/a4/a4-v2; CD=/home/danbolser/Build/molstar-chat-driver
uv run python scripts/build_rating_set.py $RUN --set a4-v2 --plan-only        # what the run offers
uv run python scripts/build_rating_set.py $RUN --set a4-v2 \
    --out $CD/site/rate/a4-v2 --key $A4/key.json --jobs 16                    # build; back the key up
git tag a4-v2-analysis                                                        # plan and analysis fixed before the first rating
# database migration, serving plan, function deploy, pictures, invitations: runbook steps 6 and 7
uv run python scripts/export_ratings.py --set a4-v2 --author "<token name>" --test "<token name>"
uv run python scripts/agreement.py $A4/key.json $A4/ratings.json \
    --json paper/a4/tables/agreement_v2.json --markdown paper/a4/tables/agreement_v2.md
```

Before the first invitation: merge molstar-chat-driver's `feat/rating-v2` and its keep-alive
branch (`feat/supabase-keepalive`), because the rating database pauses when idle; confirm
the reading rule (decision d); look at every "close" review sheet. Aim for 20 raters; 10 is
the least that gives a result. The paper's Section 5.5 describes this design; the one
`⟦PENDING: rating study⟧` tag is filled from `agreement_v2.md`.

## 8. Last checks before anything is public

```bash
uv run pytest -q
python paper/build.py --check && grep -c "PENDING" paper/molbench.md paper/si.md   # 0 and 0
git status --short                                         # clean; no key, no .env, no results/a4
git grep -n -I -e "sk-or-" -e "sk-ant-" -- . ':!*.md' | head                      # prints nothing
```

Merge `final-benchmark` into `main` by pull request (CI must pass), and tag the paper's
commit: `git tag -a paper-v1 -m "MolBench paper, preprint version" && git push origin paper-v1`.

## 9. Deposit, for a DOI

One Zenodo record, or one per item. The repository is under the MIT licence, and the paper's
availability section says so; the licence of the deposited answers and ratings is Dan's
choice at upload:

```bash
git archive --format=tar.gz -o molbench-corpus-v1.0.tar.gz corpus-v1.0           # code and corpus at the frozen tag
tar czf molbench-final-v1-archives.tar.gz runs/final-v1 results/final-v1          # every raw answer, every score file
tar czf molbench-ratings.tar.gz paper/a4/tables results/a4/a4-v2/ratings.json     # pseudonymised ratings only
sha256sum molbench-*.tar.gz > SHA256SUMS
```

Check `molbench-ratings.tar.gz` holds no rater name and no invite token before upload; the
answer key (`key.json`) goes in only once the study is closed. Upload at
<https://zenodo.org/deposit>, reserve the DOI, and put it in place of the two
`⟦PENDING: deposit …⟧` tags in `paper/sections/12_availability.md`; rebuild.

## 10. Preprint

```bash
python paper/build.py --pdf          # paper/molbench.pdf, paper/si.pdf
```

Server: arXiv, bioRxiv or ChemRxiv, all accepted by JCIM (`paper/venues.md`); which one is
Dan's choice. Put the preprint's DOI in `README.md` and in the leaderboard page.

## 11. Journal

First choice JCIM, then Digital Discovery (`paper/venues.md` has each journal's checked
requirements). For JCIM: an abstract of 3 to 4 sentences, a table-of-contents graphic, a data
and software availability statement with the DOIs of step 9, and a cover letter that names
the preprint and says what changed since it.
