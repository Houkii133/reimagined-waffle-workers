import { render, screen } from "@testing-library/react";
import HomePage from "../app/(marketing)/page";

describe("HomePage", () => {
  it("renders marketing message", () => {
    render(<HomePage />);
    expect(screen.getByText(/Find a role/i)).toBeInTheDocument();
  });
});
