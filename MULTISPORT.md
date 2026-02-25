# Multi-Sport Scoreboard Integration

## Overview
The MLB LED Scoreboard now supports displaying games from multiple sports including:
- ⚾ **MLB** (existing functionality via statsapi)
- 🏀 **NBA** (via ESPN API) ✅ **WORKING**
- 🏒 **NHL** (via ESPN API) ✅ **WORKING**
- ⚽ **Soccer** (via ESPN API) ✅ **WORKING** - Premier League & MLS
- 🏈 **NFL** (coming soon - off-season)

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
  "sports": ["NBA", "NHL", "SOCCER"],
  "favorite_teams": {
    "NBA": [
      {"name": "Milwaukee Bucks", "id": "15"},
      {"name": "Boston Celtics", "id": "2"}
    ],
    "NHL": [
      {"name": "Boston Bruins", "id": "6"},
      {"name": "Toronto Maple Leafs", "id": "10"}
    ],
    "SOCCER": [
      {"name": "Liverpool", "id": "364"},
      {"name": "Arsenal", "id": "359"}
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

**NHL Team IDs:**
- Anaheim Ducks: 24
- Arizona Coyotes: 53
- Boston Bruins: 6
- Buffalo Sabres: 7
- Calgary Flames: 20
- Carolina Hurricanes: 12
- Chicago Blackhawks: 16
- Colorado Avalanche: 21
- Columbus Blue Jackets: 29
- Dallas Stars: 25
- Detroit Red Wings: 17
- Edmonton Oilers: 22
- Florida Panthers: 13
- Los Angeles Kings: 26
- Minnesota Wild: 30
- Montreal Canadiens: 8
- Nashville Predators: 18
- New Jersey Devils: 1
- New York Islanders: 2
- New York Rangers: 3
- Ottawa Senators: 9
- Philadelphia Flyers: 4
- Pittsburgh Penguins: 5
- San Jose Sharks: 28
- Seattle Kraken: 55
- St. Louis Blues: 19
- Tampa Bay Lightning: 14
- Toronto Maple Leafs: 10
- Vancouver Canucks: 23
- Vegas Golden Knights: 54
- Washington Capitals: 15
- Winnipeg Jets: 52

**Soccer Team IDs (Premier League):**
- Arsenal: 359
- Aston Villa: 362
- Bournemouth: 349
- Brentford: 337
- Brighton & Hove Albion: 331
- Chelsea: 363
- Crystal Palace: 384
- Everton: 368
- Fulham: 370
- Ipswich Town: 373
- Leicester City: 375
- Liverpool: 364
- Manchester City: 382
- Manchester United: 360
- Newcastle United: 361
- Nottingham Forest: 393
- Southampton: 376
- Tottenham Hotspur: 367
- West Ham United: 371
- Wolverhampton Wanderers: 380

**Note:** For MLS teams, use the ESPN team search or check ESPN's MLS page for team IDs.

## What Gets Displayed

### NBA Games
The scoreboard shows:
- Team names (abbreviated to fit display)
- Current scores (for live/final games)
- Quarter/Period (Q1, Q2, Q3, Q4, OT, etc.)
- Time remaining (for live games)
- Game time (for scheduled games)
- "NBA" indicator
- Leader highlighted in red (live), winner in green (final)

### NHL Games
The scoreboard shows:
- Team names (abbreviated, e.g., BOS, TOR)
- Current scores (for live/final games)
- Period (P1, P2, P3, OT, SO)
- Time remaining (for live games)
- Game time (for scheduled games)
- "NHL" indicator
- OT/Shootout games highlighted in orange
- Leader highlighted in red (live), winner in green (final)

### Soccer/Football Games
The scoreboard shows:
- Team names (abbreviated, e.g., LIV, ARS, MUN)
- Current scores (for live/final games)
- Half/Period (1H, 2H, ET for extra time, PK for penalties)
- Match minute (e.g., "45'+2" for injury time)
- Game time (for scheduled games)
- "FOOTY" indicator
- Draws shown in white, wins in green (final)
- ET/PK matches highlighted with indicators

### Game Rotation
- Games rotate every ~15 seconds (same as MLB)
- MLB, NBA, NHL, and Soccer games are included in the rotation
- Live games from any sport are prioritized

## Architecture

### Key Files Created
- `data/models/base_game.py` - Abstract base class for all sports
- `data/models/nba_game.py` - NBA-specific game model
- `data/models/nhl_game.py` - NHL-specific game model
- `data/models/soccer_game.py` - Soccer-specific game model
- `data/providers/base_provider.py` - Provider interface
- `data/providers/espn_provider.py` - ESPN API integration (NBA, NHL, NFL)
- `data/scheduler.py` - Multi-sport game scheduler
- `data/multi_sport.py` - Integration wrapper
- `renderers/main.py` - Updated to support multi-sport rendering

### Integration Points
- `data/__init__.py`: Data class now tracks both MLB and other sport games
- `data/config/__init__.py`: Parses multi_sport configuration
- `renderers/main.py`: Renders NBA/NHL games when selected in rotation

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
