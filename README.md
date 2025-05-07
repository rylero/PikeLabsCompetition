# Politiscan

### Project Structure
![Diagram of Project Structure](docs/diagram.excalidraw.svg)

### API Choice
For this extension we use GROK completion with custom Brave Search API tooling

Speed Comparison of Models (based on analysis of this article https://www.npr.org/2025/04/22/nx-s1-5372588/trump-tariffs-imf-trade-world-economy):
| Model    | Speed |
| -------- | ------- |
| GROK-3   | 1m 17.9s |
| GROK-3-Fast | 25.57s |
| GROK-3-Mini    | 45.13s |
| GROK-3-Mini-Fast (chosen model)    | 28.46s |https://file+.vscode-resource.vscode-cdn.net/Users/ryanleroy/PikeLabsCompetition/docs/structure.excalidraw.svg

### Possible Features / TODOs
- [ ] Improve Text grabbing functionality
- [ ] Fix bug where bias and factuality descriptions don't display
- [ ] Fix inital article click where it says "No article text found on this page" (Shaun)
- [ ] Select the context menu for text grabbing
- [ ] Automatic Page loading on popular new sites
- [ ] Better loading menu / fix flow errors
- [ ] Cleaner UI
- [x] YouTube/video caption downloader? (Nathan + Ryan)
- [ ] Chat Feature to ask questions about an article
- [ ] Reduce context window size from tool call by cutting unnecessary info (Ryan)
- [x] Use Tavily search for better research (Ryan)
- [x] Speed up request by reducing the number of tool calls (Ryan)
- [ ] Switch to structured response format to prevent JSON format errors (Ryan)
- [ ] Add Show_Bias to analysis cachew
- [ ] Preload common articles for better UX

### Possible Technologies
- Readability API for extracting article text in a much more sofiticated manner: https://github.com/mozilla/readability
