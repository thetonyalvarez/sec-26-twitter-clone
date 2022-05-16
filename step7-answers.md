# Step Seven: Research and Understand Login Strategy

Look over the code in **_app.py_** related to authentication.

-   How is the logged in user being kept track of?
    -   When a user logs in (via `/login` route), the `do_login(user)` is called once the login info is validated (via `User.authenticate()` method).
    -   Inside `do_login(user)`, the user's id is assigned to the session key.
    -   The `@app.before_request` route is run before every @app route. Inside this function, the session key (which is the logged in user's id) is queried in the DB and the resulting User is assigned to the global `g.user` to be used in other routes.
-   What is Flask’s **_g_** object?
    -   **_g_** is a global namespace that holds any global data we want to use in our app context.
-   What is the purpose of **_add_user_to_g_**?
    -   Inside this function, the session key (which is the logged in user's id) is queried in the DB and the resulting User is assigned to the global `g.user` to be used in other routes.
-   What does **_@app.before_request_** mean?
    -   The `@app.before_request` route is run before every @app route.
