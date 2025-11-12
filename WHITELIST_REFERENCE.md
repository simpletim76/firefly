# Whitelist Reference Guide

This document contains additional kid-safe domains you can add to profiles as needed.

## Streaming Services (Already Included)

### Disney+
- disneyplus.com
- disney.com
- dssott.com (CDN)
- bamgrid.com (API)
- disney-plus.net (CDN)
- disneystreaming.com

### Netflix
- netflix.com
- nflxext.com
- nflximg.net (images)
- nflxvideo.net (video CDN)
- nflxso.net

## Additional Streaming Services

### Paramount+ (Nick shows)
- paramountplus.com
- cbsaavideo.com
- cbsi.com
- cbsistatic.com

### Hulu (Disney-owned)
- hulu.com
- hulustream.com
- hulu.us
- huluim.com

### Apple TV+
- tv.apple.com
- apple.com

### Amazon Prime Video
- amazon.com
- primevideo.com
- atv-ps.amazon.com
- aiv-cdn.net

## Educational Sites

### General Learning
- brainpop.com - Educational videos and quizzes
- ixl.com - Comprehensive learning platform
- prodigygame.com - Math learning game
- duolingo.com - Language learning
- typing.com - Typing practice
- typingclub.com - Typing lessons

### Science & Nature
- kids.nationalgeographic.com
- sciencekids.co.nz
- nasa.gov
- esa.int (European Space Agency)

### Math
- mathplayground.com
- mathletics.com
- splashlearn.com
- mathgames.com

### Reading & Language
- readingeggs.com
- raz-kids.com
- storylineonline.net
- epic.com (Epic! Books)

### Coding (Age 9+)
- scratch.mit.edu
- code.org
- tynker.com
- codecademy.com
- hourofcode.com

## Gaming Platforms

### General Kid-Safe
- roblox.com
- rbxcdn.com (Roblox CDN)
- minecraft.net
- mojang.com

### Educational Games
- coolmathgames.com
- funbrain.com
- pbskids.org/games
- nickjr.com/games

## Art & Creativity

### Drawing & Design
- tinkercad.com - 3D modeling
- sketchpad.app - Drawing
- pixilart.com - Pixel art

## Social (Age-Appropriate)

### Communication (Parent-supervised)
- messenger.com (Facebook Messenger)
- zoom.us (for online classes)
- meet.google.com (Google Meet)

## Essential Infrastructure Domains

### Google Services (Required for many sites)
- google.com
- googleapis.com
- gstatic.com
- googleusercontent.com
- googlesyndication.com
- doubleclick.net (ads, if allowing)

### CDN & Infrastructure
- cloudflare.com
- cloudfront.net (Amazon CDN)
- akamaihd.net (CDN)
- fastly.net (CDN)

### Authentication
- accounts.google.com
- login.live.com (Microsoft)
- appleid.apple.com

## Tips for Adding Domains

1. **Check DNS Logs**: Monitor the logs to see what domains are being blocked
2. **Start Small**: Begin with main domains, add CDN domains as needed
3. **Test Functionality**: Make sure streaming/games work after adding domains
4. **Parent Domains**: Adding `example.com` allows all `*.example.com` subdomains
5. **Temporary Enable**: Use the "Disable" feature instead of removing domains

## Common CDN Domains (Add if content doesn't load)

If images or videos aren't loading on whitelisted sites, try adding:
- akamaihd.net
- cloudfront.net
- cloudflare.com
- fastly.net
- cdninstagram.com
- fbcdn.net

## Troubleshooting

### Disney+ Not Working
Make sure all these are whitelisted:
- disneyplus.com
- dssott.com
- bamgrid.com
- disney-plus.net

### Netflix Not Working
Make sure all these are whitelisted:
- netflix.com
- nflxvideo.net
- nflxext.com
- nflxso.net

### YouTube Kids
For restricted YouTube access:
- youtube.com
- ytimg.com
- googlevideo.com
- ggpht.com

## Age-Specific Recommendations

### Ages 4-6 (Harriet's Age Group)
Focus on: PBS Kids, Nick Jr, Sesame Workshop, Starfall, ABCya

### Ages 7-9 (Aurora's Age Group)
Add: Scratch, Khan Academy, Code.org, Minecraft, basic Wikipedia

### Ages 10-12
Consider: More coding platforms, expanded Wikipedia, educational YouTube channels

## Monitoring Recommendations

1. Review DNS logs weekly
2. Discuss blocked sites with kids
3. Gradually expand whitelists as kids mature
4. Use profile colors to quickly identify traffic in logs
5. Check "Top Blocked Domains" on dashboard regularly
