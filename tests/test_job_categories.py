import unittest

from job_categories import get_resume_category


class ResumeCategoryTests(unittest.TestCase):
    def test_requested_roles_map_to_resume_categories(self):
        cases = {
            "Embedded Software Engineer": "Embedded",
            "Firmware Engineer": "Embedded",
            "Networking Engineer": "Embedded",
            "General Software Engineer": "General",
            "Backend Software Engineer": "General",
            "Python Developer": "General",
            "Machine Learning Intern": "AI/ML",
            "AI Engineering Intern": "AI/ML",
            "MLOps Intern": "AI/ML",
            "Data Engineering Intern": "AI/ML",
        }

        for title, expected_category in cases.items():
            with self.subTest(title=title):
                self.assertEqual(get_resume_category(title), expected_category)

    def test_specialized_category_takes_precedence_over_generic_software(self):
        self.assertEqual(
            get_resume_category("Embedded Software Engineer"),
            "Embedded",
        )
        self.assertEqual(
            get_resume_category("Software Engineer, Machine Learning"),
            "AI/ML",
        )
        self.assertEqual(get_resume_category("AI/ML Engineer"), "AI/ML")
        self.assertEqual(get_resume_category("Software Engineering Intern"), "General")

    def test_unmatched_titles_remain_uncategorized(self):
        self.assertIsNone(get_resume_category("Product Marketing Manager"))


if __name__ == "__main__":
    unittest.main()
