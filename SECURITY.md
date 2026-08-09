# Security

## Reporting a vulnerability

Open a GitHub security advisory on this repository, or an issue if the
problem is not sensitive. There is no SLA — this is a spare-time project.

## What this tool can do to your data

`mealie_ctx.py apply` writes to your Mealie instance through the REST API.
Some operations cannot be undone:

- `merge_food` / `merge_unit` rewrite every affected recipe and delete the
  source object.
- `delete_organizer` deletes a category, tag or tool.
- `retag_recipe` and `patch_recipe` overwrite fields on a recipe.

There is no rollback. If a run fails halfway, the actions already applied
stay applied.

**Take a backup before the first run**: Mealie -> Site Settings -> Backups.

Mitigations built into the tool: the execution order is enforced and aborts
before the first write; destructive operations are announced; `--dry-run`
shows every action without writing; there is no operation for deleting
recipes at all.

## Tokens

`MEALIE_TOKEN` is a full API token for your instance, `ANTHROPIC_API_KEY` a
billable API key. Both are read from the environment and never written to
disk by this project. Keep them out of shell history and out of the
`.actions.json` files you may keep around.

`.mealie_index.json` holds recipe names, slugs and ingredient ids of your
instance. It is gitignored, but it is not encrypted — treat it like the rest
of your recipe data.

## What leaves your machine

- Requests to your own Mealie instance.
- In standalone mode: recipe context and the rules go to the Anthropic API.
- In agent mode: whatever your IDE's model provider receives.
- `audit links --check-urls` sends one HEAD request per recipe to the
  original source domains, which tells those servers you hold that recipe.
