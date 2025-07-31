# ChangeUserPermission

This Script is meant to change the Current Students Permissions to Read Only

# How to get the Token ?
Your Profile -> Settings -> Developer Settings (Last option) -> Fine Grained Tokens 

Remember to configure to only affect the right organization

Required Token Permissions

| Org permission | Repo permission |
| --- | --- |
| **Read** and **Write** to members | **Read** to metadata |
| **Read** and **Write** to organization administration | **Read** and **Write** to administration |

PS: This token can only be seen once so if you close the tab you will have to generate a new one






.env file example : 
    GH_Token= {TOKEN}

    GH_Org= {ORG_NAME}