# MarketInsight

An AI-powered Indian stock market analysis platform that provides comprehensive financial data and intelligent insights through a conversational interface, focused on NSE/BSE markets with INR pricing.

## Overview

MarketInsight leverages advanced AI agents to deliver real-time Indian stock market information, financial analysis, and investment insights. The platform combines the power of LangChain and LangGraph with Groq's Llama 3.3 model and Yahoo Finance data to create an intelligent assistant specifically designed for Indian markets (NSE/BSE).

## Key Features

- **Indian Market Focus**: Specialized for NSE (National Stock Exchange) and BSE (Bombay Stock Exchange)
- **INR-Only Pricing**: All prices displayed in Indian Rupees (₹) for local relevance
- **Real-Time Data**: Live stock prices, market indices, and commodity prices
- **AI-Powered Analysis**: Natural language interface for querying stock information
- **Comprehensive Tools**: 18+ specialized tools for stock analysis
- **Market Insights**: Top gainers/losers, sector performance, and market movers

## Technology Stack

**Backend:**
- Python 3.x - Primary programming language
- FastAPI - High-performance API framework
- Uvicorn - ASGI server
- LangChain & LangGraph - AI agent orchestration
- Groq API (Llama 3.3 70B) - AI model for intelligent responses
- YFinance - Financial data retrieval
- Langfuse - Observability and tracing

**Frontend Options:**
- **React + TypeScript** - Modern, production-ready interface
  - TailwindCSS for styling
  - shadcn/ui components
  - Real-time streaming responses
- **Streamlit** - Python-based rapid prototyping interface
  - Quick deployment
  - Built-in data visualization

## Getting Started

### Prerequisites
- Python 3.x
- Node.js (for React frontend)
- Groq API key (free at https://console.groq.com)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/muthurajmervin/Marketinsight.git
   cd MarketInsight
   ```

2. Create and activate virtual environment
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. Install Python dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in `.env` file
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

5. Run the backend server
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup (Optional)

**Option 1: React Frontend**
```bash
cd frontend
npm install
npm run dev
```
Access at `http://localhost:5173`

**Option 2: Streamlit**
```bash
streamlit run streamlit_app.py
```
Access at `http://localhost:8501`

## Project Structure

```
MarketInsight/
├── MarketInsight/
│   ├── components/
│   │   └── agent.py          # AI agent configuration
│   └── utils/
│       ├── tools.py          # Financial data tools
│       └── logger.py         # Logging configuration
├── config/
│   └── config.py             # Pydantic models
├── frontend/                # React frontend
│   ├── src/
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── main.py                  # FastAPI backend
├── streamlit_app.py         # Streamlit alternative
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
└── README.md
```

## API Capabilities

The platform provides 18 specialized tools for comprehensive Indian stock analysis:

**Stock Analysis:**
- Stock price tracking (INR-only)
- Historical data analysis
- Company information and ratios
- Ticker/symbol lookup

**Financial Statements:**
- Balance Sheet
- Income Statement
- Cash Flow Statement

**Market Data:**
- NSE Nifty 50 and BSE Sensex indices
- Top gainers/losers (Indian stocks)
- Sector performance analysis
- Market movers

**Ownership & Insights:**
- Dividend and split history
- Institutional holders
- Mutual fund holders
- Major shareholders
- Insider transactions
- Analyst recommendations

**Commodities:**
- Gold, Silver, Oil, Natural Gas prices (INR)

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Langfuse Configuration (Optional - for observability/tracing)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

## Usage Examples

### Query Examples
- "What's the current price of Reliance Industries?"
- "Show me today's top gainers in Indian market"
- "How is Nifty 50 performing today?"
- "What's the current gold price in INR?"
- "Give me historical data for TCS for last 7 days"

### API Endpoint
```bash
POST /api/chat
Content-Type: application/json

{
  "prompt": {
    "content": "What's the current price of Reliance Industries?",
    "id": "user-message-id",
    "role": "user"
  },
  "threadId": "conversation-thread-id",
  "responseId": "response-id"
}
```

## Features

### Indian Market Focus
- NSE (National Stock Exchange) data
- BSE (Bombay Stock Exchange) data
- Popular Indian stocks: Reliance, TCS, HDFC Bank, Infosys, ICICI Bank, etc.
- INR-only pricing for Indian users

### Real-Time Data
- Live stock prices with INR conversion
- Market indices (Nifty 50, Sensex)
- Historical data analysis
- Sector performance tracking

### AI-Powered Insights
- Natural language understanding
- Context-aware responses
- Tool-calling for real-time data retrieval
- Intelligent market analysis

## Error Handling

The platform includes intelligent error handling for:
- API rate limits (Groq API)
- Data availability issues
- Invalid ticker symbols
- Network connectivity problems

## Deployment

The project is configured for deployment on:
- **Render** (render.yaml included)
- **Docker** (can be containerized)
- **Vercel** (for React frontend)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms specified in the LICENSE file.

## Acknowledgments

- Groq API for providing fast AI inference
- Yahoo Finance (via yfinance) for market data
- LangChain and LangGraph for AI agent framework
- The open-source community for the tools and libraries used