import { render, screen } from '@testing-library/react';
import App from './App';

test('renders SkillExtract title', () => {
  render(<App />);
  const heading = screen.getByText(/SkillExtract AI/i);
  expect(heading).toBeInTheDocument();
});
