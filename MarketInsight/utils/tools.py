import time
import requests
import yfinance as yf
from langchain.tools import tool
from MarketInsight.utils.logger import get_logger

logger = get_logger("Tools")

# Currency conversion rates (approximate, will be updated dynamically)
USD_TO_INR = 83.5
EUR_TO_INR = 90.2

def get_inr_price(price_usd=None, price_eur=None):
    """Convert price to Indian Rupees"""
    try:
        # Try to get current exchange rate
        try:
            usd_inr = yf.Ticker("USDINR=X").info.get("regularMarketPrice", USD_TO_INR)
            eur_inr = yf.Ticker("EURINR=X").info.get("regularMarketPrice", EUR_TO_INR)
        except:
            usd_inr = USD_TO_INR
            eur_inr = EUR_TO_INR
        
        if price_usd:
            return round(price_usd * usd_inr, 2)
        elif price_eur:
            return round(price_eur * eur_inr, 2)
        return None
    except:
        if price_usd:
            return round(price_usd * USD_TO_INR, 2)
        elif price_eur:
            return round(price_eur * EUR_TO_INR, 2)
        return None


# --------------------------------------------------------------------------------
# Tool 1: Retrieve Company Stock Price
# --------------------------------------------------------------------------------
@tool(
    'get_stock_price',
    description="A function that returns the current stock price of a given ticker"
)
def get_stock_price(ticker: str):
    logger.info(f"Retrieving Stock Price of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided."

    # Prevent invalid generic tickers
    invalid_tickers = ["NSE", "BSE", "MARKET", "STOCK", ""]

    if ticker.upper() in invalid_tickers:
        return (
            f"'{ticker}' is not a valid stock ticker. "
            "Please provide a company name or symbol."
        )

    start_time = time.time()

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        stock_price = info.get("regularMarketPrice")
        previous_close = info.get("previousClose")
        change = info.get("regularMarketChange")
        change_percent = info.get("regularMarketChangePercent")

        if stock_price is None:
            return (
                f"No stock price found for '{ticker}'. "
                "Please verify the ticker symbol."
            )

        end_time = time.time()

        logger.info(
            f"Retrieved Stock Price of {ticker} "
            f"in {end_time - start_time:.3f} seconds"
        )

        # Convert to INR
        price_inr = get_inr_price(price_usd=stock_price)
        previous_close_inr = get_inr_price(price_usd=previous_close) if previous_close else None
        change_inr = get_inr_price(price_usd=change) if change is not None else None
        company_name = info.get("shortName", ticker)
        
        response = f"**{company_name} ({ticker})**\n"
        if price_inr:
            response += f"• Current Price: ₹{price_inr:.2f}\n"
        if previous_close_inr:
            response += f"• Previous Close: ₹{previous_close_inr:.2f}\n"
        if change is not None and change_inr is not None:
            response += f"• Change: ₹{change_inr:.2f} ({change_percent:.2f}%)\n"
        
        return response

    except Exception as e:
        logger.error(
            f"Failed to retrieve stock price of "
            f"{ticker}: {str(e)}"
        )

        return (
            f"Error retrieving stock price "
            f"for {ticker}"
        )



# --------------------------------------------------------------------------------
# Tool 2: Retrieve Company Stock Historical Data
# --------------------------------------------------------------------------------
@tool('get_historical_data', description="A function that returns the historical data of a given ticker in the given start and end date")
def get_historical_data(ticker: str, start_date: str, end_date: str):
    logger.info(f"Retrieving Historical Data of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        historical_data = stock.history(start=start_date, end=end_date)
        
        if historical_data is None or historical_data.empty:
            return f"No historical data available for {ticker} in the specified date range."

        # Get company info
        try:
            company_name = stock.info.get("shortName", ticker)
        except:
            company_name = ticker

        # Format the response with detailed information
        response = f"**📊 {company_name} ({ticker}) - Historical Data**\n"
        response += f"**Period:** {start_date} to {end_date}\n\n"
        
        # Calculate some statistics
        if 'Close' in historical_data.columns:
            close_prices = historical_data['Close']
            latest_price = close_prices.iloc[-1]
            earliest_price = close_prices.iloc[0]
            price_change = latest_price - earliest_price
            percent_change = (price_change / earliest_price) * 100 if earliest_price != 0 else 0
            
            highest_price = close_prices.max()
            lowest_price = close_prices.min()
            
            # Convert to INR
            latest_inr = get_inr_price(price_usd=latest_price)
            highest_inr = get_inr_price(price_usd=highest_price)
            lowest_inr = get_inr_price(price_usd=lowest_price)
            earliest_inr = get_inr_price(price_usd=earliest_price)
            price_change_inr = get_inr_price(price_usd=price_change)
            
            response += "**📈 Price Summary:**\n"
            response += f"• Starting Price: ₹{earliest_inr:.2f}\n"
            response += f"• Ending Price: ₹{latest_inr:.2f}\n"
            response += f"• Price Change: ₹{price_change_inr:.2f} ({percent_change:+.2f}%)\n"
            response += f"• Highest Price: ₹{highest_inr:.2f}\n"
            response += f"• Lowest Price: ₹{lowest_inr:.2f}\n\n"
        
        # Show recent data points
        response += "**📅 Recent Price Points:**\n"
        recent_data = historical_data.tail(7) if len(historical_data) >= 7 else historical_data
        for date, row in recent_data.iterrows():
            close_price = row['Close'] if 'Close' in row else None
            if close_price:
                price_inr = get_inr_price(price_usd=close_price)
                response += f"• {date.strftime('%Y-%m-%d')}: ₹{price_inr:.2f}\n"
        
        # Volume information if available
        if 'Volume' in historical_data.columns:
            avg_volume = historical_data['Volume'].mean()
            response += f"\n**📊 Trading Volume:**\n"
            response += f"• Average Volume: {avg_volume:,.0f} shares\n"

        end_time = time.time()
        logger.info(f"Retrieved Historical Data of {ticker} in {end_time - start_time:.3f} seconds")
        
        return response

    except Exception as e:
        logger.error(f"Failed to retrieve historical data of {ticker}: {str(e)}")
        return "Error: Failed to retrieve historical data. Please try again later."


# --------------------------------------------------------------------------------
# Tool 3: Retrieve Company Stock News
# --------------------------------------------------------------------------------
@tool('get_stock_news', description="A function that returns the news of a given ticker")
def get_stock_news(ticker: str):
    logger.info(f"Retrieving News of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        news = stock.news

        if news is None:
            return "No news available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved News of {ticker} in {end_time - start_time:.3f} seconds")
        return news

    except Exception as e:
        logger.error(f"Failed to retrieve news of {ticker}: {str(e)}")
        return "Error: Failed to retrieve news. Please try again later."


# --------------------------------------------------------------------------------
# Tool 4: Retrieve Company's Balance Sheet
# --------------------------------------------------------------------------------
@tool('get_balance_sheet', description="A function that returns the balance sheet of a given ticker")
def get_balance_sheet(ticker: str):
    logger.info(f"Retrieving Balance Sheet of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet.to_dict()

        if balance_sheet is None:
            return "No balance sheet available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Balance Sheet of {ticker} in {end_time - start_time:.3f} seconds")
        return balance_sheet

    except Exception as e:
        logger.error(f"Failed to retrieve balance sheet of {ticker}: {str(e)}")
        return "Error: Failed to retrieve balance sheet. Please try again later."


# --------------------------------------------------------------------------------
# Tool 5: Retrieve Company's Income Statement
# --------------------------------------------------------------------------------
@tool('get_income_statement', description="A function that returns the income statement of a given ticker")
def get_income_statement(ticker: str):
    logger.info(f"Retrieving Income Statement of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        income_statement = stock.financials.to_dict()

        if income_statement is None:
            return "No income statement available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Income Statement of {ticker} in {end_time - start_time:.3f} seconds")
        return income_statement

    except Exception as e:
        logger.error(f"Failed to retrieve income statement of {ticker}: {str(e)}")
        return "Error: Failed to retrieve income statement. Please try again later."
    

# --------------------------------------------------------------------------------
# Tool 6: Retrieve Company's Cash Flow Statement
# --------------------------------------------------------------------------------
@tool('get_cash_flow', description="A function that returns the cash flow statement of a given ticker")
def get_cash_flow(ticker: str):
    logger.info(f"Retrieving Cash Flow of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        cash_flow = stock.cashflow.to_dict()

        if cash_flow is None:
            return "No cash flow available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Cash Flow of {ticker} in {end_time - start_time:.3f} seconds")
        return cash_flow

    except Exception as e:
        logger.error(f"Failed to retrieve cash flow of {ticker}: {str(e)}")
        return "Error: Failed to retrieve cash flow. Please try again later."

# --------------------------------------------------------------------------------
# Tool 7: Retrieve Company Info & Ratios
# --------------------------------------------------------------------------------
@tool('get_company_info', description="A function that returns company profile and key financial ratios")
def get_company_info(ticker: str):
    logger.info(f"Retrieving Company Info of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        info = stock.info

        if info is None:
            return "No company info available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Company Info of {ticker} in {end_time - start_time:.3f} seconds")
        return info

    except Exception as e:
        logger.error(f"Failed to retrieve company info of {ticker}: {str(e)}")
        return "Error: Failed to retrieve company info. Please try again later."

# --------------------------------------------------------------------------------
# Tool 8: Retrieve Dividend History
# --------------------------------------------------------------------------------
@tool('get_dividends', description="A function that returns the dividend payment history of a given ticker")
def get_dividends(ticker: str):
    logger.info(f"Retrieving Dividends of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        dividends = stock.dividends.to_dict()

        if dividends is None:
            return "No dividends available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Dividends of {ticker} in {end_time - start_time:.3f} seconds")
        return dividends

    except Exception as e:
        logger.error(f"Failed to retrieve dividends of {ticker}: {str(e)}")
        return "Error: Failed to retrieve dividends. Please try again later."

# --------------------------------------------------------------------------------
# Tool 9: Retrieve Stock Split History
# --------------------------------------------------------------------------------
@tool('get_splits', description="A function that returns the stock split history of a given ticker")
def get_splits(ticker: str):
    logger.info(f"Retrieving Stock Splits of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        splits = stock.splits.to_dict()

        if splits is None:
            return "No stock splits available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Stock Splits of {ticker} in {end_time - start_time:.3f} seconds")
        return splits

    except Exception as e:
        logger.error(f"Failed to retrieve stock splits of {ticker}: {str(e)}")
        return "Error: Failed to retrieve stock splits. Please try again later."


# --------------------------------------------------------------------------------
# Tool 10: Retrieve Institutional Holders
# --------------------------------------------------------------------------------
@tool('get_institutional_holders', description="A function that returns the institutional ownership data of a given ticker")
def get_institutional_holders(ticker: str):
    logger.info(f"Retrieving Institutional Holders of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        holders = stock.institutional_holders.to_dict()

        if holders is None:
            return "No institutional holders available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Institutional Holders of {ticker} in {end_time - start_time:.3f} seconds")
        return holders

    except Exception as e:
        logger.error(f"Failed to retrieve institutional holders of {ticker}: {str(e)}")
        return "Error: Failed to retrieve institutional holders. Please try again later."

# --------------------------------------------------------------------------------
# Tool 11: Retrieve Major Share Holders
# --------------------------------------------------------------------------------
@tool('get_major_shareholders', description="A function that returns the major share holder data of a given ticker")
def get_major_shareholders(ticker: str):
    logger.info(f"Retrieving Major Share Holders of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        holders = stock.major_holders.to_dict()

        if holders is None:
            return "No major share holders available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Major Share Holders of {ticker} in {end_time - start_time:.3f} seconds")
        return holders

    except Exception as e:
        logger.error(f"Failed to retrieve major share holders of {ticker}: {str(e)}")
        return "Error: Failed to retrieve major share holders. Please try again later."

# --------------------------------------------------------------------------------
# Tool 12: Retrieve Mutual Fund Holders
# --------------------------------------------------------------------------------
@tool('get_mutual_fund_holders', description="A function that returns the mutual fund ownership data of a given ticker")
def get_mutual_fund_holders(ticker: str):
    logger.info(f"Retrieving Mutual Fund Holders of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        holders = stock.mutualfund_holders.to_dict()

        if holders is None:
            return "No mutual fund holders available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Mutual Fund Holders of {ticker} in {end_time - start_time:.3f} seconds")
        return holders

    except Exception as e:
        logger.error(f"Failed to retrieve mutual fund holders of {ticker}: {str(e)}")
        return "Error: Failed to retrieve mutual fund holders. Please try again later."

# --------------------------------------------------------------------------------
# Tool 13: Retrieve Insider Transactions
# --------------------------------------------------------------------------------
@tool('get_insider_transactions', description="A function that returns the insider buy/sell transactions of a given ticker")
def get_insider_transactions(ticker: str):
    logger.info(f"Retrieving Insider Transactions of {ticker}")

    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        insider_txn = stock.insider_transactions.to_dict()

        if insider_txn is None:
            return "No insider transactions available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Insider Transactions of {ticker} in {end_time - start_time:.3f} seconds")
        return insider_txn

    except Exception as e:
        logger.error(f"Failed to retrieve insider transactions of {ticker}: {str(e)}")
        return "Error: Failed to retrieve insider transactions. Please try again later."

# --------------------------------------------------------------------------------
# Tool 14: Retrieve Analyst Recommendations
# --------------------------------------------------------------------------------
@tool('get_analyst_recommendations', description="A function that returns the analyst recommendations of a given ticker")
def get_analyst_recommendations(ticker: str):
    logger.info(f"Retrieving Analyst Recommendations of {ticker}")
    
    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        recommendations = stock.recommendations.to_dict()

        if recommendations is None:
            return "No analyst recommendations available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Analyst Recommendations of {ticker} in {end_time - start_time:.3f} seconds")
        return recommendations

    except Exception as e:
        logger.error(f"Failed to retrieve analyst recommendations of {ticker}: {str(e)}")
        return "Error: Failed to retrieve analyst recommendations. Please try again later."

# --------------------------------------------------------------------------------
# Tool 15: Retrieve Analyst Recommendations Summary
# --------------------------------------------------------------------------------
@tool('get_analyst_recommendations_summary', description="A function that returns the analyst recommendations summary of a given ticker")
def get_analyst_recommendations_summary(ticker: str):
    logger.info(f"Retrieving Analyst Recommendations Summary of {ticker}")
    
    if not ticker or not isinstance(ticker, str):
        return "Error: Invalid ticker provided. Please provide a valid ticker symbol."

    try:
        start_time = time.time()
        stock = yf.Ticker(ticker)
        recommendations = stock.recommendations_summary.to_dict()

        if recommendations is None:
            return "No analyst recommendations summary available for {ticker}"

        end_time = time.time()
        logger.info(f"Retrieved Analyst Recommendations Summary of {ticker} in {end_time - start_time:.3f} seconds")
        return recommendations

    except Exception as e:
        logger.error(f"Failed to retrieve analyst recommendations summary of {ticker}: {str(e)}")
        return "Error: Failed to retrieve analyst recommendations summary. Please try again later."

# --------------------------------------------------------------------------------
# Tool 16: Retrieve Company's Ticker/Symbol
# --------------------------------------------------------------------------------
@tool(
    'get_ticker',
    description="Returns the stock ticker/symbol of a company"
)
def get_ticker(company_name: str):
    logger.info(
        f"Retrieving Ticker of {company_name}"
    )

    if (
        not company_name or
        not isinstance(company_name, str)
    ):
        return (
            "Error: Invalid company name."
        )

    try:
        start_time = time.time()

        url = (
            "https://query2.finance.yahoo.com/"
            f"v1/finance/search?q={company_name}"
        )

        response = requests.get(url)

        if response.status_code != 200:
            return (
                "Failed to retrieve ticker."
            )

        data = response.json()

        quotes = data.get("quotes", [])

        if not quotes:
            return (
                f"No ticker found for "
                f"{company_name}"
            )


        # Skip invalid generic symbols
        invalid_symbols = ["NSE", "BSE"]

        ticker = None

        for quote in quotes:
            symbol = quote.get("symbol")

            if symbol and symbol.upper() not in invalid_symbols:
                ticker = symbol
                break

        if not ticker:
            return f"No valid ticker found for {company_name}"


        end_time = time.time()

        logger.info(
            f"Retrieved Ticker of "
            f"{company_name} in "
            f"{end_time - start_time:.3f} seconds"
        )

        return str(ticker)

    except Exception as e:
        logger.error(
            f"Failed to retrieve ticker of "
            f"{company_name}: {str(e)}"
        )

        return (
            "Error: Failed to retrieve ticker."
        )


# --------------------------------------------------------------------------------
# Tool 15: Get Market Indices Data
# --------------------------------------------------------------------------------
@tool('get_market_indices', description="A function that returns current data for major Indian market indices like NSE Nifty 50, BSE Sensex")
def get_market_indices(indices: str = "^NSEI,^BSESN"):
    logger.info(f"Retrieving Market Indices Data")

    try:
        start_time = time.time()
        
        # Default indices: NSE Nifty 50, BSE Sensex
        index_list = indices.split(',') if indices else ["^NSEI", "^BSESN"]
        
        results = {}
        for index in index_list:
            try:
                index = index.strip()
                stock = yf.Ticker(index)
                info = stock.info
                
                index_name = info.get("shortName", index)
                current_price = info.get("regularMarketPrice")
                previous_close = info.get("previousClose")
                change = info.get("regularMarketChange")
                change_percent = info.get("regularMarketChangePercent")
                
                if current_price:
                    price_inr = get_inr_price(price_usd=current_price)
                    previous_close_inr = get_inr_price(price_usd=previous_close) if previous_close else None
                    change_inr = get_inr_price(price_usd=change) if change is not None else None
                    results[index_name] = {
                        "symbol": index,
                        "current_price": current_price,
                        "price_inr": price_inr,
                        "previous_close": previous_close,
                        "previous_close_inr": previous_close_inr,
                        "change": change,
                        "change_inr": change_inr,
                        "change_percent": change_percent
                    }
            except Exception as e:
                logger.error(f"Failed to get data for {index}: {str(e)}")
                continue

        end_time = time.time()
        logger.info(f"Retrieved Market Indices in {end_time - start_time:.3f} seconds")
        
        if not results:
            return "Unable to retrieve market indices data at this time."
        
        # Format the response with detailed information
        response = "**📊 MAJOR MARKET INDICES**\n\n"
        for index_name, data in results.items():
            response += f"**{index_name} ({data['symbol']})**\n"
            if data['price_inr']:
                response += f"• Current Price: ₹{data['price_inr']:.2f}\n"
            if data['previous_close_inr']:
                response += f"• Previous Close: ₹{data['previous_close_inr']:.2f}\n"
            if data['change'] is not None and data['change_inr'] is not None:
                change_symbol = "+" if data['change'] > 0 else ""
                response += f"• Change: {change_symbol}₹{data['change_inr']:.2f} ({data['change_percent']:.2f}%)\n"
            response += "\n"
        
        return response

    except Exception as e:
        logger.error(f"Failed to retrieve market indices: {str(e)}")
        return "Error: Failed to retrieve market indices data. Please try again later."


# --------------------------------------------------------------------------------
# Tool 16: Get Top Gainers/Losers
# --------------------------------------------------------------------------------
@tool('get_market_movers', description="A function that returns top gainers and losers from major market indices by analyzing popular stocks")
def get_market_movers():
    logger.info("Retrieving Market Movers (Gainers/Losers)")

    try:
        start_time = time.time()
        
        # List of popular Indian stocks across different sectors to analyze
        popular_stocks = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",  # Large Cap
            "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS",  # Major Stocks
            "AXISBANK.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",  # Diversified
            "TATAMOTORS.NS", "NTPC.NS", "POWERGRID.NS", "WIPRO.NS", "TITAN.NS",  # Various Sectors
        ]
        
        stock_data = []
        
        for ticker in popular_stocks:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                current_price = info.get("regularMarketPrice")
                previous_close = info.get("previousClose")
                change_percent = info.get("regularMarketChangePercent")
                company_name = info.get("shortName", ticker)
                
                if current_price and change_percent is not None:
                    price_inr = get_inr_price(price_usd=current_price)
                    stock_data.append({
                        "ticker": ticker,
                        "name": company_name,
                        "current_price": current_price,
                        "price_inr": price_inr,
                        "change_percent": change_percent,
                        "market_cap": info.get("marketCap"),
                        "volume": info.get("regularMarketVolume"),
                        "sector": info.get("sector", "N/A")
                    })
                    
            except Exception as e:
                logger.error(f"Failed to get data for {ticker}: {str(e)}")
                continue
        
        # Sort by change percent to find gainers and losers
        stock_data.sort(key=lambda x: x["change_percent"], reverse=True)
        
        # Get top 5 gainers and losers
        top_gainers = stock_data[:5]
        top_losers = stock_data[-5:] if len(stock_data) >= 5 else stock_data[-len(stock_data):]
        top_losers.reverse()  # Show worst performers first
        
        end_time = time.time()
        logger.info(f"Market movers analysis completed in {end_time - start_time:.3f} seconds")
        
        if not stock_data:
            return "Unable to retrieve stock performance data at this time. Please try again later."
        
        # Format the response with detailed information
        response = "**📈 TOP GAINERS TODAY**\n\n"
        for i, stock in enumerate(top_gainers, 1):
            response += f"{i}. **{stock['name']} ({stock['ticker']})**\n"
            if stock['price_inr']:
                response += f"   • Current Price: ₹{stock['price_inr']:.2f}\n"
            response += f"   • Change: +{stock['change_percent']:.2f}%\n"
            if stock['sector'] != "N/A":
                response += f"   • Sector: {stock['sector']}\n"
            if stock['market_cap']:
                market_cap_inr = get_inr_price(price_usd=stock['market_cap'])
                response += f"   • Market Cap: ₹{market_cap_inr:,.0f}\n"
            response += "\n"
        
        response += "**📉 TOP LOSERS TODAY**\n\n"
        for i, stock in enumerate(top_losers, 1):
            response += f"{i}. **{stock['name']} ({stock['ticker']})**\n"
            if stock['price_inr']:
                response += f"   • Current Price: ₹{stock['price_inr']:.2f}\n"
            response += f"   • Change: {stock['change_percent']:.2f}%\n"
            if stock['sector'] != "N/A":
                response += f"   • Sector: {stock['sector']}\n"
            if stock['market_cap']:
                market_cap_inr = get_inr_price(price_usd=stock['market_cap'])
                response += f"   • Market Cap: ₹{market_cap_inr:,.0f}\n"
            response += "\n"
        
        response += "*Note: Based on analysis of major popular stocks across different sectors. For comprehensive market movers data, check financial news websites.*"
        
        return response

    except Exception as e:
        logger.error(f"Failed to retrieve market movers: {str(e)}")
        return "Error: Failed to retrieve market movers data. Please try again later."


# --------------------------------------------------------------------------------
# Tool 17: Get Sector Performance
# --------------------------------------------------------------------------------
@tool('get_sector_performance', description="A function that returns performance data for different market sectors using sector ETFs")
def get_sector_performance():
    logger.info("Retrieving Sector Performance")

    try:
        start_time = time.time()
        
        # Sector ETFs representing different market sectors
        sector_etfs = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Financials": "XLF",
            "Energy": "XLE",
            "Consumer Discretionary": "XLY",
            "Consumer Staples": "XLP",
            "Industrials": "XLI",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Materials": "XLB",
            "Communication": "XLC"
        }
        
        sector_data = []
        
        for sector, etf in sector_etfs.items():
            try:
                stock = yf.Ticker(etf)
                info = stock.info
                
                current_price = info.get("regularMarketPrice")
                previous_close = info.get("previousClose")
                change_percent = info.get("regularMarketChangePercent")
                
                if current_price and change_percent is not None:
                    price_inr = get_inr_price(price_usd=current_price)
                    sector_data.append({
                        "sector": sector,
                        "etf": etf,
                        "current_price": current_price,
                        "price_inr": price_inr,
                        "change_percent": change_percent
                    })
                    
            except Exception as e:
                logger.error(f"Failed to get data for {sector} ({etf}): {str(e)}")
                continue
        
        # Sort by performance
        sector_data.sort(key=lambda x: x["change_percent"], reverse=True)
        
        end_time = time.time()
        logger.info(f"Sector performance analysis completed in {end_time - start_time:.3f} seconds")
        
        if not sector_data:
            return "Unable to retrieve sector performance data at this time."
        
        # Format the response with detailed information
        response = "**🏭 SECTOR PERFORMANCE ANALYSIS**\n\n"
        
        # Best performing sectors
        response += "**🔥 TOP PERFORMING SECTORS**\n"
        for i, sector in enumerate(sector_data[:5], 1):
            response += f"{i}. **{sector['sector']}** ({sector['etf']})\n"
            response += f"   • Current Price: ${sector['current_price']:.2f}\n"
            if sector['price_inr']:
                response += f"   • Price in INR: ₹{sector['price_inr']:.2f}\n"
            response += f"   • Change: +{sector['change_percent']:.2f}%\n\n"
        
        # Worst performing sectors
        response += "**📉 UNDERPERFORMING SECTORS**\n"
        worst_sectors = sector_data[-5:] if len(sector_data) >= 5 else sector_data[-len(sector_data):]
        worst_sectors.reverse()
        for i, sector in enumerate(worst_sectors, 1):
            response += f"{i}. **{sector['sector']}** ({sector['etf']})\n"
            response += f"   • Current Price: ${sector['current_price']:.2f}\n"
            if sector['price_inr']:
                response += f"   • Price in INR: ₹{sector['price_inr']:.2f}\n"
            response += f"   • Change: {sector['change_percent']:.2f}%\n\n"
        
        return response

    except Exception as e:
        logger.error(f"Failed to retrieve sector performance: {str(e)}")
        return "Error: Failed to retrieve sector performance data. Please try again later."


# --------------------------------------------------------------------------------
# Tool 18: Get Commodity Prices (Gold, Silver, Oil, etc.)
# --------------------------------------------------------------------------------
@tool('get_commodity_price', description="A function that returns current prices for commodities like gold, silver, oil, etc.")
def get_commodity_price(commodity: str = "gold"):
    logger.info(f"Retrieving Commodity Price for {commodity}")

    try:
        start_time = time.time()
        
        # Commodity symbols
        commodity_symbols = {
            "gold": "GC=F",
            "silver": "SI=F",
            "oil": "CL=F",
            "crude oil": "CL=F",
            "natural gas": "NG=F",
            "copper": "HG=F",
            "platinum": "PL=F"
        }
        
        commodity_lower = commodity.lower()
        symbol = commodity_symbols.get(commodity_lower, "GC=F")  # Default to gold
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            current_price = info.get("regularMarketPrice")
            previous_close = info.get("previousClose")
            change = info.get("regularMarketChange")
            change_percent = info.get("regularMarketChangePercent")
            
            if current_price is None:
                return f"Unable to retrieve current price for {commodity}. Please try again later."
            
            # Convert to INR
            price_inr = get_inr_price(price_usd=current_price)
            previous_close_inr = get_inr_price(price_usd=previous_close) if previous_close else None
            change_inr = get_inr_price(price_usd=change) if change is not None else None
            
            # Format response
            response = f"**💰 {commodity.upper()} Price Information**\n\n"
            if price_inr:
                response += f"**Current Price:** ₹{price_inr:.2f}\n"
            if previous_close_inr:
                response += f"**Previous Close:** ₹{previous_close_inr:.2f}\n"
            if change is not None and change_inr is not None:
                change_symbol = "+" if change > 0 else ""
                response += f"**Change:** {change_symbol}₹{change_inr:.2f} ({change_percent:+.2f}%)\n"
            
            # Add some context
            response += f"\n**📊 Trading Symbol:** {symbol}\n"
            response += "*Note: Commodity prices are for futures contracts and may differ from spot prices.*"
            
            end_time = time.time()
            logger.info(f"Retrieved {commodity} price in {end_time - start_time:.3f} seconds")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to retrieve {commodity} price: {str(e)}")
            return f"Error: Unable to retrieve {commodity} price at this time. Please try again later."

    except Exception as e:
        logger.error(f"Failed to retrieve commodity price: {str(e)}")
        return "Error: Failed to retrieve commodity price data. Please try again later."
