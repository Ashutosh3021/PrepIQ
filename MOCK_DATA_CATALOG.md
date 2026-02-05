# PrepIQ Mock Data Catalog

## Current State Analysis

This document catalogs all mock data and hardcoded values in the PrepIQ frontend codebase that need to be migrated to real API calls.

## Identified Mock Data Locations

### 1. Prediction Pages
**Files**: `app/predictions/page.tsx`, `app/protected/predictions/page.tsx`

**Mock Data Found**:
- Hardcoded prediction data object with:
  - Confidence score: 85
  - Summary text
  - 3 sample questions with:
    - Fixed question texts
    - Mock marks, units, probabilities
    - Appearance years [2020, 2022, 2024]
    - Fixed expected answers
  - Topic heatmap data (Matrix Theory, Linear Transformations, etc.)
  - Study recommendations with hardcoded dates
  - Performance trend data with hardcoded month/score arrays

### 2. User Profile/Settings Pages
**Files**: `app/protected/settings/page.tsx`, `app/protected/profile/page.tsx`, `components/user-nav.tsx`

**Mock Data Found**:
- John Doe placeholder names in:
  - User navigation dropdown (user-nav.tsx)
  - Settings page display
  - Profile page
- Hardcoded user data defaults in state initialization
- Static profile information

### 3. Subjects Pages
**Files**: `app/subjects/page.tsx`, `app/protected/subjects/page.tsx`

**Mock Data Found**:
- Initial empty array state
- Form default values
- Search functionality without backend filtering

### 4. Dashboard Pages
**Files**: `app/dashboard/page.tsx`, `app/protected/page.tsx`

**Mock Data Found**:
- Static dashboard statistics
- Placeholder performance metrics
- Fixed greeting messages ("Hi Ashu!")
- Static recent activity data

### 5. Analysis Pages
**Files**: `app/protected/analysis/page.tsx`

**Mock Data Found**:
- Static performance trend data
- Fixed chart data arrays
- Hardcoded Recharts data

### 6. Questions Pages
**Files**: `app/protected/questions/page.tsx`

**Mock Data Found**:
- Static important questions list
- Fixed question data
- Hardcoded difficulty levels and importance ratings

### 7. Auth Pages
**Files**: `app/login/page.tsx`, `app/signup/page.tsx`

**Mock Data Found**:
- Mostly using real API calls already
- Some hardcoded validation patterns

## API Migration Requirements

### Required API Endpoints:

1. **User Profile Data**
   - `GET /auth/profile` - Current user profile (already implemented)
   - `GET /api/users/me` - Alternative user info endpoint

2. **Prediction Data**
   - `GET /api/predictions/latest` - Current prediction results
   - `GET /api/predictions/trend` - Performance trend data
   - `GET /api/predictions/topics` - Topic probability data
   - `GET /api/predictions/recommendations` - Study recommendations

3. **Dashboard Data**
   - `GET /api/dashboard/stats` - User statistics
   - `GET /api/dashboard/recent-activity` - Recent activity feed
   - `GET /api/dashboard/progress` - Study progress metrics

4. **Subjects Data**
   - `GET /api/subjects` - User's subjects
   - `GET /api/subjects/{id}` - Individual subject details
   - `POST /api/subjects` - Create new subject
   - `PUT /api/subjects/{id}` - Update subject
   - `DELETE /api/subjects/{id}` - Delete subject

5. **Questions Data**
   - `GET /api/questions/important` - Important questions list
   - `GET /api/questions/search` - Search questions by criteria

## Implementation Plan

### Phase 1: Authentication and User Data
- Replace mock user profile data with real API calls
- Update user-nav component to fetch real user data
- Add proper loading and error states

### Phase 2: Prediction Pages
- Create new API endpoints for prediction data
- Replace static prediction data with fetch calls
- Implement proper chart data transformation

### Phase 3: Dashboard Components
- Replace static dashboard data with API calls
- Add skeleton loaders and proper error handling
- Implement data caching where appropriate

### Phase 4: Analysis and Questions Pages
- Connect to real API endpoints
- Replace static data arrays
- Add data filtering and search functionality

### Phase 5: Cleanup and Testing
- Remove unused components and files
- Update dependencies and remove unused packages
- Run comprehensive testing

## Type Safety Requirements

### Current Types That Need Update:

```typescript
interface UserData {
  full_name: string;
  email: string;
  college_name: string;
  program: string;
  year_of_study: number;
  // ... existing fields
}

interface PredictionData {
  confidence: number;
  summary: string;
  questions: PredictionQuestion[];
  topicHeatmap: TopicHeatMapEntry[];
  studyRecommendations: string[];
  // ... add timestamp fields
}

interface PredictionQuestion {
  id: string;
  number: number;
  text: string;
  marks: number;
  unit: string;
  probability: string;
  appearedIn: number[];
  difficulty: string;
  expectedAnswer: string;
  // ... add from backend schema
}

interface ChartDataPoint {
  month: string;
  score: number;
  // ... other fields for Recharts
}

interface DashboardStats {
  subjects: number;
  progress: number;
  recentTests: number;
  avgScore: number;
  // ... real metrics from API
}
```

## Timeline Estimates

1. **User Data Migration**: 2-3 hours
2. **Prediction API Integration**: 4-6 hours
3. **Dashboard Migration**: 3-4 hours
4. **Subject/QA Migration**: 2-3 hours
5. **Cleanup and Testing**: 2-3 hours
6. **Documentation Updates**: 1-2 hours

**Total Estimated Time**: 14-19 hours for complete migration

## Verification Criteria

Before and after migration:
- ✅ No more hardcoded user data
- ✅ All chart data comes from API
- ✅ Proper error handling and loading states
- ✅ Real authentication with Supabase tokens
- ✅ All CRUD operations work with real API
- ✅ Build compiles successfully
- ✅ No TypeScript errors
- ✅ No unused imports/files

## Testing Strategy

1. **Unit Tests**: Mock API calls during testing
2. **Integration Tests**: Real API endpoints with test database
3. **UI Tests**: Verify components work with real/fake data
4. **Regression Tests**: Ensure existing functionality works after migration

## Post-Migration Documentation Updates Required

- ✅ README.md needs updated features section
- ✅ Architecture diagrams with API calls
- ✅ Installation and setup instructions
- ✅ Development workflow with backend

---
**Generated on**: 2025-01-06  
**Next Update**: After phase completion reviews