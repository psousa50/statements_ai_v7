✅ UI Design - User Home Page

Project: Bank Statement Visualizer
Page: Logged-In Home Page (Dashboard Entry)
Tech: React + Tailwind CSS
Purpose: Utility-focused home for users who have logged in and uploaded one or more bank statements.

⸻

🧩 Page Layout

1. Top Navbar
	•	Left: Logo or app name (“StatementApp”).
	•	Right: Navigation links:
	•	Dashboard
	•	Upload
	•	Categories
	•	Reports
	•	Account (dropdown: Profile, Settings, Logout)
	•	Fixed with light background and shadow.

⸻

2. Welcome Section
	•	Text: “Welcome back, [FirstName]!”
	•	Optional: last upload info (“Last upload: 5 days ago”)

⸻

3. Quick Upload Widget
	•	Card with:
	•	Upload button
	•	Drag & drop area
	•	Formats supported: PDF, CSV, XLS
	•	Small helper text: “Your file will be analyzed and categorized automatically.”

⸻

4. Key Metrics Cards (grid of 3 or 4 cards)

Each card has:
	•	Title
	•	Big value
	•	Optional small chart or icon
	•	Examples:
	•	💸 Total spent this month
	•	🧠 % auto-categorized
	•	🏷️ Most common category
	•	📄 Number of uploaded statements

⸻

5. Recent Activity Feed
	•	Vertical list or table of:
	•	Upload file name
	•	Upload date
	•	Number of transactions
	•	Status (Processed / In Progress / Failed)
	•	Button: “View All Statements”

⸻

6. Insights Preview
	•	Small charts or visuals:
	•	Pie chart of spending by category
	•	Bar chart of top merchants or recurring expenses

⸻

7. Footer
	•	Basic footer with app name and links (Contact, Terms, Privacy)

⸻

🧠 Style Guidelines
	•	Clean, light layout
	•	Tailwind bg-white, shadow, rounded-2xl, p-4 for cards
	•	Responsive grid layout
	•	Use text-gray-600/800 for clarity
	•	Highlight CTAs in indigo or blue