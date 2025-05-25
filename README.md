# COMP639_Project_1_CMV
### Developed by CMV Group: Jiajun Liu, James Yeon, Evgeniia Dubovskaia, Jingyi Sun, Wenhui Zhang
___

**SYNC – Save Your New travel Content Travel Journal — a platform for travellers to create and share their travel stories   .**

Travel Journal is a digital diary platform for travellers to record, organise, and (optionally) share their journeys. Users can document individual trips, break them down into events, and upload notes and photos. Journeys may remain private or be made public to inspire and inform fellow travellers.

The app currently supports three user roles:

- **Traveller** (default)
- **Editor**
- **Admin**



## Run this app

To run the Travel Journal:

1. Open the project in Visual Studio Code.
2. Create a virtual environment using the following commands:

```bash
python3 -m venv venv
```

It'll create a folder called `venv`.

Activate virtual environment with:

Windows
```bash
venv/scripts/activate
```

Linux / MacOS:
```bash
source venv/bin/activate
```

3. Install all of the packages listed in requirements.txt 

```bash
(venv) pip install -r requirements.txt
```

4. Use the [Database Creation Script](create_database.sql) to create 
    the **Travel_Journal_CMV** database.
5. Use the [Database Population Script](populate_database.sql) to populate
   the **Travel_Journal_CMV** ***users***, ***journeys***, and ***events*** tables with data.
6. Modify [connect.py](app/connect.py) with the connection details for
   your local database server.
7. Run [The Python/Flask application](run.py).

After the last step new user can be registred as a new **traveller**. 
However, existing credendials may be used to log in the system. 
There is a range of existing users groupped by roles:

- 20 **travellers**: "traveller1", "traveller2", ... "traveller20"
- 5 **editors**: "editor1", "editor2", ... "editor5"
- 2 **admins**: "admin1", "admin2"

All listed accounts have the same password: **password123456**



## General functions

All users can use the login and registration forms, regardless of their role. 
However, due to the session management and user role system, different roles 
have different features in the application. Below is a summary of the features 
available for each role.

## Traveller functions

- Register and log in
- Maintain a personal profile with optional photo, name, location, and description
- Change password and personal details
- Create/edit/delete journeys (private by default)
- Set journeys to public visibility
- Add/edit/delete events to journeys with date/time, location, image
- View and search public journeys by title and description


## Editor functions

**The editor role can only be assigned by an administrator.**
- All traveller features except deleting of journey and event
- Edit public journeys and events (title, description, date, location)
- Remove photo of the event in case of inappropriate content

## Administrators functions

**Administrators have the most extensive features on the site. Only an existing administrator 
can assign the administrator role to a user.**

- All editor features
- Promote or demote users to any role
- Ban or reactivate user account
- Set warning to the user for inappropriate content or behavior
- View all users and manage accounts
- View and manage list of editors and admins
- Search user profiles by name, email, last name, first name and full name
