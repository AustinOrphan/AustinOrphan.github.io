# CSS Reorganization Plan for main.css

## Current Issues
1. Styles are scattered throughout the file
2. Media queries are mixed with base styles
3. Some sections have unclear boundaries
4. Duplicate or similar rules exist
5. Comments are inconsistent

## Proposed Structure

### 1. **CSS Variables & Root** (Lines 1-30)
- Color variables
- Custom properties
- Global settings

### 2. **Base Styles & Resets** (Lines 31-100)
- Universal selector reset
- HTML/Body styles
- Background textures/patterns

### 3. **Typography** (Lines 101-150)
- Font imports
- Heading styles
- Paragraph styles
- Text utilities

### 4. **Layout Containers** (Lines 151-200)
- Page wrapper
- Content wrapper
- Section containers

### 5. **Components** (Lines 201-500)
- Buttons
- Cards
- Forms
- Icons

### 6. **Navigation** (Lines 501-650)
- LinkBar
- Section navigation
- Mobile navigation

### 7. **Sections** (Lines 651-1200)
- Hero section
- Projects section
- About section
- Contact section

### 8. **Footer** (Lines 1201-1350)
- Footer layout
- Footer social links
- Back to top button

### 9. **Animations & Keyframes** (Lines 1351-1500)
- All @keyframes definitions
- Animation utilities

### 10. **Utility Classes** (Lines 1501-1600)
- Helper classes
- Display utilities
- Spacing utilities

### 11. **Easter Eggs** (Lines 1601-1900)
- 8-bit mode styles
- Special effects

### 12. **Media Queries** (Lines 1901-end)
- Mobile first approach
- Breakpoint: 600px
- Breakpoint: 768px
- Breakpoint: 1024px

## Benefits
1. Easier to find and modify styles
2. Better maintainability
3. Reduced duplicate code
4. Clear section boundaries
5. Consistent commenting

## Implementation Steps
1. Add clear section headers
2. Group related styles
3. Move all media queries to the end
4. Consolidate duplicate rules
5. Add consistent comments