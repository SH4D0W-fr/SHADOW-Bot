ServerID = 1460609497344250085
ServerName = "SHADOW Dev"


WelcomeChannelID = 1460637521695211662
WelcomeMessage = "Bienvenue sur le serveur, {member}!"
GoodbyeChannelID = 1460637539563208714
GoodbyeMessage = "Au revoir, {member} ! Tu vas nous manquer."

LogsChannel = 1461276988865253500
LogsEnabled = True

TicketChannel = 1461708320434950335

TicketAutoPingRole = 1461709099774509169 # When users with this role send a message, the bot will ping the author of the ticket

TicketAutoCloseDelay = 12  # Auto close time when a staff answer and ther isnt response from user, in hours

TicketTypes = {
    "test1": {
        "name": "Test 1",
        "description": "Description du ticket de test 1",
        "category_id": 1461708362042314938,
        "staff_roles_id": [1461708434402443274, 1461709099774509169],
        "roles_to_ping": [1461708434402443274]
    },
    "test2": {
        "name": "Test 2",
        "description": "Description du ticket de test 2",
        "category_id": 1461708362042314938,
        "staff_roles_id": [1461708434402443274, 1461709099774509169],
        "roles_to_ping": [1461708434402443274]
    }
}