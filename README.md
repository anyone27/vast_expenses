# Vast Expenses
#### Video Demo:  https://youtu.be/5nRhzWlJAvM
#### Description: Vast Expenses is an expense and receipt/invoice amalgamation tool for small business and self employed.

Vast expenses allows users to create an account, create projects which they are overseeing and assign expenses to each of these projects separately. Each project has a title and a description as well as a total of the amount spent on expenses, all displayed on a handy dashboard.

Each project can have multiple expenses created and assigned to it, all stored in a SQLite3 database. The expenses have a description, the amount spent and the date when the expense was made as well as allowing the user to upload a picture of the receipt for later reference and accounting purposes.

The pictures uploaded are stored on the server rather than as BLOB's in the database and are automatically deleted when the expenses or projects are deleted by the user.

Users are able to edit the projects and the expenses and the Dashboard and Expenses Summary page will update accordingly.

The Vast Expenses web application was built using Python and the Flask microframework as well as HTML, CSS and a small amount of Javascript.

I originally used various files to organise blueprints and routes for each of the features, as is documented in the tutorial on the Flask documentation, however I was having issues with this as the expenses are nested within the projects and rely on passing through the project_id to identify which expenses are attached. I ended up having all the routes and functions outlined in a single app.py file as this was a simpler approach and due to the relative simplicity of the app, was not too overwhelming.

The app.py file includes functions and routes for:

- Registering a user
 - including checking if a username is already taken
 - hashing the users Password
- Logging the user in
- Logging the user out
- Enforcing Log in required for various areas of the website
- Displaying a home/landing page which:
 - Instructs a user to register or log in on arrival if not already
 - displays a Dashboard showing all projects created by the user and a total of expenses assigned to each projects
- Fetching projects depending on User Id
- Creating and updating projects
- Deleting projects and their associated expenses and uploaded images
- Fetching expenses according to associated Project Id
- Listing a summary of expenses for a project
- Creating, updating and deleting expenses
- checking for allowed file extensions (currently not working)
- Uploading files to the server and fetching them to display on the website.
