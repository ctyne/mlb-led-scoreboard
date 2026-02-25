# Multi-Sport Scoreboard Integration

## Overview
The MLB LED Scoreboard now supports displaying games from multiple sports including:
- ⚾ **MLB** (existing functionality via statsapi)
- 🏀 **NBA** (via ESPN API)
- 🏒 **NHL** (coming soon)
- 🏈 **NFL** (coming soon)
- ⚽ **Soccer** (coming soon)

## How It Works

### Data Sources
- **MLB**: Uses the existing `statsapi` library
- **Other Sports**: Uses ESPN's free public API (no authentication required)

### Game Prioritization
When cycling through games, the scoreboard prioritizes:
1. **Live games** (any sport) - shown first
2. **Scheduled games** - sorted by start time
3. **Final games** - shown last

### Configuration

Add this section to your `config.json`:

```json
"multi_sport": {
  "enabled": true,
  "sports": ["NBA"],
  "favorite_teams": {
    "NBA": [
      {"name": "Milwaukee Bucks", "id": "15"},
      {"name": "Boston Celtics", "id": "2"}
    ]
  },
  "api_provider": "espn"
}
```

### Finding Team IDs

**NBA Team IDs:**
- Atlanta Hawks: 1
- Boston Celtics: 2
- Brooklyn Nets: 17
- Charlotte Hornets: 30
- Chicago Bulls: 4
- Cleveland Cavaliers: 5
- Dallas Mavericks: 6
- Denver Nuggets: 7
- Detroit Pistons: 8
- Golden State Warriors: 9
- Houston Rockets: 10
- Indiana Pacers: 11
- LA Clippers: 12
- Los Angeles Lakers: 13
- Memphis Grizzlies: 29
- Miami Heat: 14
- Milwaukee Bucks: 15
- Minnesota Timberwolves: 16
- New Orleans Pelicans: 3
- New York Knicks: 18
- Oklahoma City Thunder: 25
- Orlando Magic: 19
- Philadelphia 76ers: 20
- Phoenix Suns: 21
- Portland Trail Blazers: 22
- Sacramento Kings: 23
- San Antonio Spurs: 24
- Toronto Raptors: 28
- Utah Jazz: 26
- Washington Wizards: 27

## What Gets Displayed

### NBA Games
The scoreboard shows:
- Team names (abbreviated to fit display)
- Current scores (for live/final games)
- Quarter/Period (Q1, Q2, Q3, Q4, OT, etc.)
- Time remaining (for live games)
- Game time (for scheduled games)
- "NBA" indicator

### Game Rotation
- Games rotate every ~15 seconds (same as MLB)
- Both MLB and NBA games are included in the rotation
- Live games from any sport are prioritized

## Architecture

### Key Files Created
- `data/models/base_game.py` - Abstract base class for all sports
- `data/models/nba_game.py` - NBA-specific game model
- `data/providers/base_provider.py` - Provider interface
- `data/providers/espn_provider.py` - ESPN API integration
- `data/scheduler.py` - Multi-sport game scheduler
- `data/multi_sport.py` - Integration wrapper
- `renderers/games/nba.py` - NBA game renderer
- `renderers/main.py` - Updated to support multi-sport

### Integration Points
- `data/__init__.py`: Data class now tracks both MLB and other sport games
- `data/config/__init__.py`: Parses multi_sport configuration
- `renderers/main.py`: Renders NBA games when selected in rotation

## Testing on Raspberry Pi

1. **Edit your config.json:**
   ```bash
   nano ~/mlb-led-scoreboard/config.json
   ```

2. **Add the multi_sport section** (see example above)

3. **Restart the scoreboard:**
   ```bash
   sudo systemctl restart mlb-led-scoreboard
   ```

4. **Check logs:**
   ```bash
   sudo journalctl -u mlb-led-scoreboard -f
   ```

Look for messages like:
```
Found 6 other sport games
```

## Limitations / Future Work

### Current Limitations
- Only NBA is fully implemented
- NHL, NFL, Soccer coming soon
- No sport-specific stats yet (fouls, power plays, etc.)
- Uses simple text-based renderer

### Planned Enhancements
- Sport-specific renderers with better layouts
- Team logos for each sport
- Sport indicators/icons
- Advanced stats (fouls, power plays, downs, etc.)
- Support for NHL, NFL, Soccer

## Technical Details

### ESPN API
- Base URL: `http://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard`
- No API key required (public API)
- Real-time live scores
- Supports: NBA, NHL, NFL, MLB, Soccer

### Caching
- Game data is cached for 5 minutes during live games
- Prevents excessive API calls
- Automatically refreshes when needed

## Troubleshooting

**Q: Multi-sport not showing?**
- Check `config.json` has `"enabled": true`
- Verify team IDs are correct
- Check logs for errors

**Q: Only seeing MLB games?**
- Make sure you have favorite teams configured
- Check that games are happening today
- Verify ESPN API is accessible

**Q: Games not updating?**
- Check internet connection
- Verify ESPN API is responding
- Look for error messages in logs

## Example Output

```
NBA
MIL 108
CLE 105
Q4 2:34

⚾ MLB game...

NBA
BOS 95
DEN 92
FINAL
```

## Credits
- ESPN API: https://github.com/pseudo-r/Public-ESPN-API
- Original MLB Scoreboard: https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard
