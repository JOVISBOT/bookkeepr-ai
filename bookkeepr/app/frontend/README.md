# BookKeepr Phase 3 - Dashboard & Analytics

This directory contains the React frontend for the BookKeepr AI Dashboard and Analytics.

## Features

### Dashboard
- **Summary Cards**: Total transactions, pending review, AI accuracy, monthly spending
- **Charts**: Monthly spending bar chart, category breakdown pie chart, accuracy trend line chart
- **Confidence Distribution**: Visual breakdown of high/medium/low confidence categorizations
- **Quick Actions**: Direct links to review queue and AI categorization

### Transactions Page
- **Transaction Table**: Sortable, filterable table with search
- **Status Badges**: Color-coded status (categorized, suggested, uncategorized)
- **Confidence Scoring**: Visual indicators for AI confidence levels
- **Pagination**: Server-side pagination with navigation controls

### Review Queue
- **Approval/Review Interface**: Approve, reject, or correct AI categorizations
- **Confidence Filtering**: Filter by confidence level (high/medium/low)
- **Bulk Actions**: Multi-select for batch approvals
- **Category Selector**: Dropdown to correct miscategorized transactions

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS 4** - Styling
- **Recharts** - Data visualization
- **TanStack Query** - Server state management
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icons

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── dashboard/     # Dashboard-specific components
│   │   │   ├── StatCard.tsx
│   │   │   ├── SpendingChart.tsx
│   │   │   ├── CategoryChart.tsx
│   │   │   └── AccuracyChart.tsx
│   │   ├── layout/        # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Layout.tsx
│   │   ├── transactions/  # Transaction components
│   │   │   ├── TransactionTable.tsx
│   │   │   └── ReviewQueue.tsx
│   │   └── ui/            # Reusable UI components
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Badge.tsx
│   │       ├── Input.tsx
│   │       └── Select.tsx
│   ├── hooks/             # React Query hooks
│   │   ├── useTransactions.ts
│   │   └── useCompanies.ts
│   ├── lib/               # Utilities
│   │   ├── api.ts         # API client
│   │   └── utils.ts       # Formatting utilities
│   ├── pages/             # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── Transactions.tsx
│   │   └── ReviewPage.tsx
│   ├── types/             # TypeScript types
│   │   └── index.ts
│   ├── App.tsx            # Main app component
│   └── main.tsx           # Entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

## API Integration

The frontend connects to the Flask backend API at `/api/v1/`:

- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/{id}/transactions` - Get transactions
- `GET /api/v1/companies/{id}/review-queue` - Get review queue
- `POST /api/v1/transactions/{id}/review` - Review transaction
- `POST /api/v1/companies/{id}/ai-categorize` - Run AI categorization
- `GET /api/v1/companies/{id}/ai-metrics` - Get AI metrics

## Development

```bash
# Install dependencies
npm install

# Start dev server (with proxy to Flask backend)
npm run dev

# Build for production
npm run build
```

## Build Output

The production build is output to `dist/` folder. Flask serves these static files via the route handler in `app/__init__.py`.

## Responsive Design

The dashboard is fully responsive:
- **Desktop**: Full sidebar + content grid
- **Tablet**: Condensed layout
- **Mobile**: Collapsible sidebar (future enhancement)

## Future Enhancements

- Real-time transaction updates via WebSockets
- Export to CSV/Excel
- Advanced filtering and date range selection
- User preferences and customization
- Dark mode support
