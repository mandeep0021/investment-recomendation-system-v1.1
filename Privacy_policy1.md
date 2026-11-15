# Privacy Policy

Last updated: 13 November 2026

## Scope

This policy describes the local educational Investment Recommendation System. It is not a substitute for a privacy review before the app is publicly hosted.

## Information processed

- The app does not ask for a name, email address, password, or account registration.
- Ticker symbols, the optional benchmark, and the selected history period are used to request market data from Yahoo Finance's public chart endpoint. The data provider receives the request from the machine or host running the app and applies its own privacy and data-handling practices.
- Returned price history is cached in the running app's memory for up to 15 minutes. The app does not write market requests, portfolios, or reports to a persistent database.
- Reports and CSV files are generated for the current session. When downloaded, they are saved by the browser to the location selected by the user.
- Streamlit's anonymous usage statistics are disabled in this project's configuration. Streamlit still uses the technical session mechanisms required to operate the app.

## Hosting and third parties

When run locally, market-data requests originate from the user's machine. If the app is hosted later, the hosting provider may process connection data or retain server logs under its own policy. A public deployment requires a renewed privacy review and clear hosting details.

Yahoo Finance is an independent third party. Its availability, data, and handling practices are outside this app's control.

## User choices

Do not enter personal or confidential information in ticker or benchmark fields. Close the app to end the local session. Downloaded files remain under the user's control.

This local project does not provide an account, contact form, or configured privacy contact address. A public release must add an appropriate owner contact channel before launch.
