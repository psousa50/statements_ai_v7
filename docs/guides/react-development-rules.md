# React (with Vite) Development Rules

## File & Folder Structure

- Use `src/` as the base directory. Group by **feature/domain** rather than by type.
- Use the following recommended structure:

```
src/
├── components/        # Reusable shared components
├── features/          # Domain-specific feature modules
│   └── user/          
│       ├── UserPage.tsx
│       ├── userSlice.ts
│       └── api.ts
├── hooks/             # Custom reusable hooks
├── lib/               # Utility functions and wrappers
├── pages/             # Route-level components (if using file-based routing)
├── styles/            # Global styles and tokens
├── App.tsx
├── main.tsx
```

## Component Conventions

- Use **function components** with hooks — never class components.
- Prefer `const` components:

```tsx
// ✅
const UserCard: React.FC<UserCardProps> = ({ user }) => {
  return <div>{user.name}</div>;
};
```

- Co-locate styles with the component (e.g., `UserCard.module.css`).

## Hooks Rules

- Follow the **Rules of Hooks**:
  - Only call hooks at the top level.
  - Only call hooks from React functions.

- Extract logic-heavy or stateful behavior into **custom hooks**:

```tsx
function useUserData(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);
  return user;
}
```

## State Management

- Prefer **React context** or **local state** for simple cases.
- Use [Zustand](https://zustand-demo.pmnd.rs/), Redux Toolkit, or similar for shared, cross-cutting state.
- Never use raw Redux without `redux-toolkit`.

## Forms

- Use [React Hook Form](https://react-hook-form.com) for complex forms.
- Always validate with a schema (`zod` or `yup`).

## Routing

- Use [React Router v6](https://reactrouter.com/en/main) with file-based routing if applicable.
- Use `useNavigate`, `useParams`, and lazy-loaded routes.
- Avoid hardcoding URLs; use route helpers.

## CSS and Styling

- Use **CSS Modules** (`*.module.css`) for most component styles.
- Use global styles only in `index.css` or `App.css`.
- Tailwind CSS is acceptable but must be documented and consistent across the team.

## Vite Configuration Rules

- Keep `vite.config.ts` minimal and declarative.
- Configure aliases using `resolve.alias`:

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
});
```

- Use `.env` files for environment variables (`.env.local`, `.env.production`).
  - All Vite env vars must start with `VITE_`

## Testing

- Use [Vitest](https://vitest.dev/) for unit and component tests.
- Use [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) for DOM interaction tests.
- File naming convention: `*.test.tsx`

```tsx
// Example test
test('renders user name', () => {
  render(<UserCard user={{ name: 'Alice' }} />);
  expect(screen.getByText('Alice')).toBeInTheDocument();
});
```

## Naming Conventions

- Components: `PascalCase`
- Files: `PascalCase.tsx` for components, `kebab-case.ts` for utils
- Hooks: `useCamelCase.ts`
- Test files: `*.test.ts(x)`

## Performance Best Practices

- Use `React.memo` for pure UI components.
- Use `useCallback` and `useMemo` to prevent unnecessary re-renders.
- Lazy-load heavy components and routes with `React.lazy`.

## Accessibility (a11y)

- Use semantic HTML elements (`<button>`, `<label>`, `<nav>`, etc.)
- Ensure all interactive elements are keyboard-navigable.
- Use `aria-*` attributes when necessary.
- Run [eslint-plugin-jsx-a11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y)

## Dev Tools & Extensions

- ESLint with `eslint-plugin-react`, `react-hooks`, `jsx-a11y`
- Prettier for consistent formatting
- Vite Plugin React Refresh (for fast refresh)
