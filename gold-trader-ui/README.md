# Gold Trader UI

Angular frontend for XAUUSD Gold Trading System with proprietary chart library.

## Features

- **Real-time Trading Dashboard**: Live price charts, trading signals, and position management
- **Smart Money Concepts Visualization**: FVG, Order Blocks, Liquidity Sweeps, Market Structure
- **Proprietary Chart Library**: Custom-built charting solution optimized for trading analysis
- **Responsive Design**: Mobile-friendly interface with Angular Material
- **Real-time WebSocket Integration**: Live price feeds and trade updates
- **Authentication & Security**: JWT-based auth with role-based access control
- **Performance Analytics**: Comprehensive trading metrics and reporting

## Technology Stack

- **Frontend**: Angular 17, TypeScript, SCSS
- **Charts**: Proprietary canvas-based charting library
- **UI Framework**: Angular Material for consistent design
- **State Management**: RxJS for reactive data flow
- **Build Tool**: Angular CLI with Docker support

## Project Structure

```
gold-trader-ui/
├── src/
│   ├── app/
│   │   ├── app.module.ts
│   │   ├── app.component.ts
│   │   ├── app-routing.module.ts
│   │   └── shared/
│   │       ├── material.module.ts
│   │       └── index.ts
│   ├── core/
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   ├── api.service.ts
│   │   │   └── websocket.service.ts
│   │   ├── guards/
│   │   │   └── auth.guard.ts
│   │   └── models/
│   │       ├── auth.models.ts
│   │       └── trading.models.ts
│   ├── features/
│   │   ├── dashboard/
│   │   ├── trading/
│   │   ├── signals/
│   │   ├── analytics/
│   │   └── settings/
│   ├── libs/
│   │   └── proprietary-charts/
│   │       ├── src/
│   │       │   ├── lib/
│   │       │   │   ├── chart.component.ts
│   │       │   ├── chart.module.ts
│   │       │   └── index.ts
│   ├── environments/
│   │   ├── environment.ts
│   │   └── environment.prod.ts
│   ├── styles.scss
│   ├── index.html
│   └── main.ts
├── Dockerfile.frontend
├── docker-compose.frontend.yml
├── nginx.frontend.conf
├── package.json
├── angular.json
├── tsconfig.json
└── README.md
```

## Development Setup

1. **Install Dependencies**:
   ```bash
   cd gold-trader-ui
   npm install
   ```

2. **Development Server**:
   ```bash
   npm start
   ```

3. **Production Build**:
   ```bash
   npm run build:prod
   ```

## Docker Deployment

1. **Build Frontend Image**:
   ```bash
   docker build -f docker-compose.frontend.yml frontend
   ```

2. **Run with Backend**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.frontend.yml up
   ```

## Key Features

### Proprietary Chart Library

- **Canvas-based Rendering**: High-performance chart rendering
- **Smart Money Concepts**: Built-in FVG, Order Block, Liquidity visualization
- **Drawing Tools**: Trend lines, Fibonacci, rectangles
- **Multi-timeframe Support**: M1, M5, M15, M30, H1, H4, D1
- **Technical Indicators**: MA, RSI, MACD, Bollinger Bands
- **Real-time Updates**: WebSocket integration for live data

### Authentication & Security

- **JWT Authentication**: Secure token-based auth
- **Role-based Access**: Admin, Trader, Viewer roles
- **Permission System**: Granular permissions for different features
- **Session Management**: Automatic token refresh and timeout handling

### Real-time Features

- **WebSocket Integration**: Live price feeds and updates
- **Signal Notifications**: Real-time trading alerts
- **Trade Management**: Live position monitoring
- **Account Updates**: Real-time balance and equity tracking

## Configuration

Environment-specific configuration for development and production environments, including API endpoints, WebSocket URLs, and feature flags.

## Integration

Seamlessly integrates with existing XAUUSD Gold Trading System backend through REST API and WebSocket connections.