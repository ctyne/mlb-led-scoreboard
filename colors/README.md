These JSON files are used to determine the colors for pretty much every element that's rendered.

# Custom Colors

You can edit these colors to display parts of the scoreboard in any way you choose.

During installation (see the main README for setup instructions), custom config files (e.g., `teams.json`, `scoreboard.json`) are created from their corresponding schema files (e.g., `teams.schema.json`, `scoreboard.schema.json`). You can then edit the custom files to override any values you want to change.

## Examples

> [!WARNING]
> **DO NOT** edit or remove `.schema` files!

**Customizing team colors:**
1. After installation, edit `teams.json` and change the `"r"`, `"g"`, and `"b"` values for the colors you wish to change
2. Your customized colors will always take precedence over the schema defaults

**Customizing scrolling text color:**
1. After installation, edit the `"final" -> "scrolling_text"` keys in `scoreboard.json` to your liking
2. Your customized colors will always take precedence over the schema defaults

**Creating additional color configurations:**
If you want multiple color configurations (e.g., for different themes like `teams.night.json`), see the migrations documentation in the main README.
