# Perturbation coverage

Share of pooled bios that each condition actually changes (unchanged bios have an identical counterfactual, so their score gap is 0 by construction).

| split | condition | bios | % changed | % changed F | % changed M | mean changes when changed |
|---|---|---|---|---|---|---|
| dev | pronoun_swap | 6906 | 98.9 | 99.2 | 98.7 | 3.09 |
| dev | name_swap_us | 6906 | 19.0 | 17.5 | 20.4 | 1.63 |
| dev | name_swap_in | 6906 | 19.0 | 17.5 | 20.4 | 1.63 |
| dev | name_in_same_gender | 6906 | 19.0 | 17.5 | 20.4 | 1.63 |
| dev | affiliation_swap | 6906 | 0.3 | 0.5 | 0.1 | 1.05 |
| dev | agentic_communal | 6906 | 2.3 | 2.3 | 2.2 | 1.07 |
| dev | gender_full | 6906 | 99.1 | 99.3 | 99.0 | 3.40 |
| test | pronoun_swap | 16217 | 99.0 | 99.1 | 98.9 | 3.09 |
| test | name_swap_us | 16217 | 19.5 | 17.4 | 21.6 | 1.60 |
| test | name_swap_in | 16217 | 19.5 | 17.4 | 21.6 | 1.60 |
| test | name_in_same_gender | 16217 | 19.5 | 17.4 | 21.6 | 1.60 |
| test | affiliation_swap | 16217 | 0.3 | 0.5 | 0.1 | 1.04 |
| test | agentic_communal | 16217 | 2.5 | 2.6 | 2.5 | 1.04 |
| test | gender_full | 16217 | 99.3 | 99.3 | 99.3 | 3.40 |

## Name pools

- **us F** (200): Abigail, Alexandra, Alice, Alicia, Alison, Allison, Alyssa, Amanda, Amber, Amy, Andrea, Angela, Anita, Ann, Anna, Anne, Annette, April, Ashley, Audrey, Barbara, Beth, Betty, Beverly, Bonnie, Brandi, Brandy, Brenda, Brianna, Brittany, Brooke, Caitlin, Carla, Carol, Caroline, Carolyn, Carrie, Cassandra, Catherine, Cathy ...
- **us M** (200): Aaron, Adam, Alan, Albert, Alejandro, Alexander, Alfred, Allen, Andrew, Anthony, Antonio, Arthur, Austin, Barry, Benjamin, Bernard, Billy, Brad, Bradley, Brandon, Brent, Brian, Bruce, Bryan, Caleb, Calvin, Carl, Carlos, Chad, Charles, Christopher, Clarence, Clayton, Clifford, Cody, Colin, Connor, Craig, Curtis, Daniel ...
- **in F** (100): Aarti, Aditi, Aishwarya, Amrita, Ananya, Anasuya, Anjali, Anjana, Anju, Ankita, Antara, Anu, Anuradha, Anushka, Aparna, Archana, Arpita, Aruna, Arundhati, Asha, Ayesha, Chitra, Deepa, Deepali, Deepika, Deepti, Devika, Geeta, Geetanjali, Hema, Ila, Indira, Isha, Ishita, Jagdeep, Jyoti, Kalpana, Kamala, Kavita, Kumari ...
- **in M** (100): Abbas, Abdul, Abhimanyu, Abhishek, Aditya, Ajay, Ajit, Akash, Akshay, Alok, Amar, Anand, Anant, Anil, Anup, Arjun, Arun, Arvind, Ashok, Atul, Avinash, Baba, Bharat, Darshan, Debendra, Deepak, Devendra, Dinesh, Gaurav, Gautam, Gian, Gopal, Hari, Jagannath, Jai, Jitendra, Kailash, Kamal, Kapil, Karan ...
