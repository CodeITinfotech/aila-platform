# AILA Design System

## Overview

The AILA Design System provides a comprehensive set of guidelines, components, and patterns for building consistent, accessible, and beautiful user interfaces across all AILA platforms.

## Brand Identity

### Logo

```
AILA Logo Usage:
- Primary: Full logo with icon + text
- Icon Only: For favicons, app icons, small spaces
- Minimum Size: 24px height
- Clear Space: 1x the logo height on all sides
```

### Brand Colors

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| Primary | #6366F1 | rgb(99, 102, 241) | CTAs, links, highlights |
| Primary Dark | #4F46E5 | rgb(79, 70, 229) | Hover states |
| Primary Light | #818CF8 | rgb(129, 140, 248) | Backgrounds |
| Secondary | #10B981 | rgb(16, 185, 129) | Success, progress |
| Accent | #F59E0B | rgb(245, 158, 11) | Warnings, badges |
| Error | #EF4444 | rgb(239, 68, 68) | Errors |
| Background | #FFFFFF | rgb(255, 255, 255) | Light mode bg |
| Background Dark | #111827 | rgb(17, 24, 39) | Dark mode bg |

## Typography

### Font Family

**Primary Font:** Inter

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### Type Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| H1 | 48px | 700 | 1.2 |
| H2 | 36px | 700 | 1.25 |
| H3 | 30px | 600 | 1.3 |
| H4 | 24px | 600 | 1.35 |
| H5 | 20px | 600 | 1.4 |
| H6 | 18px | 600 | 1.4 |
| Body | 16px | 400 | 1.6 |
| Body Small | 14px | 400 | 1.5 |
| Caption | 12px | 400 | 1.4 |

## Spacing

### Base Unit: 4px

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Tight spacing |
| sm | 8px | Small gaps |
| md | 16px | Standard spacing |
| lg | 24px | Section gaps |
| xl | 32px | Large gaps |
| 2xl | 48px | Major sections |
| 3xl | 64px | Page margins |

## Components

### Buttons

```jsx
// Button Variants
<Button variant="primary">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="danger">Danger</Button>

// Button Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// Button States
<Button loading>Saving...</Button>
<Button disabled>Disabled</Button>
<Button icon={<Icon />}>With Icon</Button>
```

### Cards

```jsx
// Card Component
<Card>
  <Card.Header>
    <Card.Title>Course Title</Card.Title>
  </Card.Header>
  <Card.Body>
    Course description and content
  </Card.Body>
  <Card.Footer>
    <Button>Enroll Now</Button>
  </Card.Footer>
</Card>
```

### Forms

```jsx
// Form Components
<Input label="Email" type="email" placeholder="Enter email" />
<Select label="Country" options={countries} />
<Checkbox label="Remember me" />
<Radio.Group options={options} />
<Textarea label="Message" rows={4} />
```

### Navigation

```jsx
// Bottom Navigation (Mobile)
<BottomNav>
  <BottomNav.Item icon={<Home />} label="Home" />
  <BottomNav.Item icon={<Book />} label="Courses" active />
  <BottomNav.Item icon={<Bot />} label="AI Tutor" />
  <BottomNav.Item icon={<User />} label="Profile" />
</BottomNav>

// Side Navigation (Web)
<SideNav>
  <SideNav.Group label="Learning">
    <SideNav.Item icon={<Home />} href="/dashboard">Dashboard</SideNav.Item>
    <SideNav.Item icon={<Book />} href="/courses">Courses</SideNav.Item>
  </SideNav.Group>
</SideNav>
```

### Modals

```jsx
<Modal
  isOpen={isOpen}
  onClose={onClose}
  title="Confirm Action"
>
  <Modal.Body>
    Are you sure you want to proceed?
  </Modal.Body>
  <Modal.Footer>
    <Button variant="ghost" onClick={onClose}>Cancel</Button>
    <Button onClick={onConfirm}>Confirm</Button>
  </Modal.Footer>
</Modal>
```

## Layouts

### Page Layouts

```jsx
// Dashboard Layout
<DashboardLayout>
  <Sidebar />
  <TopBar />
  <main>
    <Outlet />
  </main>
</DashboardLayout>

// Course Layout
<CourseLayout>
  <CourseSidebar />
  <CourseContent>
    <LessonPlayer />
  </CourseContent>
</CourseLayout>
```

### Grid System

```jsx
// Responsive Grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  <Card />
  <Card />
  <Card />
  <Card />
</div>
```

## Animations

### Micro-interactions

| Interaction | Duration | Easing | Effect |
|-------------|----------|--------|--------|
| Button press | 150ms | ease-out | Scale to 0.98 |
| Card hover | 200ms | ease-out | Shadow elevation |
| Modal open | 300ms | ease-out | Fade + scale |
| Page transition | 400ms | ease-in-out | Slide |
| Loading | 1000ms | linear | Rotate |

### Animation Tokens

```css
:root {
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-decelerate: cubic-bezier(0, 0, 0.2, 1);
  --ease-accelerate: cubic-bezier(0.4, 0, 1, 1);
}
```

## Accessibility

### Guidelines

1. **Color Contrast**: 4.5:1 for text, 3:1 for UI elements
2. **Focus Indicators**: 2px outline with 2px offset
3. **Touch Targets**: Minimum 44x44px
4. **Screen Readers**: ARIA labels and roles
5. **Keyboard Navigation**: Full functionality without mouse

### Implementation

```jsx
// Accessible Button
<button
  type="button"
  onClick={handleClick}
  aria-label="Close modal"
  aria-expanded={isOpen}
  className="focus-visible:ring-2 focus-visible:ring-primary"
>
  <Icon aria-hidden="true" />
</button>

// Loading State
<div role="status" aria-label="Loading">
  <Spinner />
  <span className="sr-only">Loading...</span>
</div>
```

## Dark Mode

### Color Tokens

```css
:root {
  --color-bg: #ffffff;
  --color-text: #111827;
  --color-surface: #f9fafb;
}

[data-theme="dark"] {
  --color-bg: #111827;
  --color-text: #f9fafb;
  --color-surface: #1f2937;
}
```

### Implementation

```jsx
// Theme Provider
<ThemeProvider defaultTheme="system">
  <App />
</ThemeProvider>

// Use Theme
const { theme, setTheme } = useTheme();

// Toggle Button
<Button
  variant="ghost"
  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
>
  {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
</Button>
```

## Responsive Breakpoints

| Breakpoint | Width | Devices |
|------------|-------|---------|
| xs | < 480px | Mobile S |
| sm | 480-767px | Mobile L |
| md | 768-1023px | Tablet |
| lg | 1024-1279px | Desktop |
| xl | 1280-1535px | Desktop L |
| 2xl | ≥ 1536px | Desktop XL |

---

*Design System Version: 1.0*
