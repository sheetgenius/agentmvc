# Questions

Answer every question from the code in this directory only. For each answer, cite the file path and the function, method or module where the rule is implemented.

1. How is an article's slug generated, and does it change when the article's title is updated?
2. When someone registers with an email or username that's already taken, what HTTP status and response body do they get, and where is that decided?
3. Which articles appear in `GET /api/articles/feed`, and in what order?
4. How is `favoritesCount` computed for an article in a response?
5. What happens, as an HTTP status and response body, when a user tries to delete a comment they didn't write?
6. What happens to a user's `bio` when an update sends an empty string?
7. How are an article's tags stored in the database, and what does `GET /api/tags` return (ordering, duplicates)?
8. What are the default and maximum values of the `limit` query parameter on article lists? If there is no maximum, say so.
9. How is the authentication token created, what does it contain, and when does it expire?
10. Where is the rule enforced that only an article's author can update or delete it? Give the file and function.
11. In an article update, what is the difference between omitting `tagList` and sending `"tagList": null`?
12. How are passwords stored, and which library does it?
