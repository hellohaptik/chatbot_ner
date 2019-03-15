### Steps for writing code and Raise a PR:

1. Fork the repo by going to https://github.com/hellohaptik/chatbot_ner.git and doing the below:
   ![Screen Shot 2019 03 14 at 4 02 57 PM](/Users/Ranvijay/Downloads/Screen Shot 2019 03 14 at 4 02 57 PM.png)

   Above will open a prompt like this:
   ![Screen Shot 2019 03 14 at 4 05 46 PM](/Users/Ranvijay/Downloads/Screen Shot 2019 03 14 at 4 05 46 PM.png)

   Click on your username or organization you own. 

2. So, now you have forked the chatbot_ner repository as shown below:
   ![Screen Shot 2019-03-14 at 4.10.13 PM](/Users/Ranvijay/Desktop/Screen Shot 2019-03-14 at 4.10.13 PM.png)

   Lets see what you need to do next:

   1. Clone your new forked repository on your machine, for me it would be something like:
      git clone https://github.com/ranvijayj/chatbot_ner.git

   2. Remember, chatbot_ner follows GitFlow so all changes unless a hot fix go to develop first.
      

   3. Checkout to new branch
      git checkout -b branch_name

      Note: branch_name to be replace with the branch name you want. Ideally it should be the name of the feature and the change e.g.: language_support_hindi

   4. Make code changes. 
      git commit -am"This change will add hindi language support etc. "
      git push origin branch_name

      

3. Create a pull request against the hellohaptik chatbot_ner repository. While creating the PR take care of the following things as shown below:
   ![Screen Shot 2019 03 14 at 5 51 43 PM](/Users/Ranvijay/Downloads/Screen Shot 2019 03 14 at 5 51 43 PM.png)

   Add Title, Description, Labels, and Milestone if you're working on any mentioned in the repository milestones. 

   **List of appropriate labels**:
   new-feature
   bug-fixes
   documentation
   enhancement
   needs-migration
   packages-updated
   miscellaneous

4. You're done. Just wait for the PR checks to pass as shown below:
   ![Screen Shot 2019-03-14 at 6.11.35 PM](/Users/Ranvijay/Downloads/Screen Shot 2019-03-14 at 6.11.35 PM.png)

    One of the admins will approve your PR and merge it. 