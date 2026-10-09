# Error analysis: esco (SkillSpan dev, 3174 sentences)

- predictions: 1188; in sentences with no gold span at all: 519 (43.7%)
- false positives by source: {'esco': 612}

## Top false-positive strings (no overlap with any gold span)

| count | text |
|---|---|
| 21 | finance |
| 19 | financial |
| 18 | leading |
| 17 | lead |
| 16 | right |
| 16 | java |
| 15 | devops |
| 13 | design |
| 13 | danish |
| 12 | be responsible |
| 9 | plan |
| 9 | personal development |
| 8 | python |
| 8 | communication |
| 8 | proteomics |
| 8 | medicine |
| 7 | english |
| 6 | agile |
| 6 | typescript |
| 6 | security |
| 6 | protein |
| 6 | project management |
| 5 | cool |
| 5 | hear |
| 5 | source |
| 5 | energy |
| 5 | customer service |
| 4 | saas |
| 4 | javascript |
| 4 | heard |
| 4 | email |
| 4 | choose |
| 4 | scrum |
| 4 | r&d |
| 4 | survey |
| 4 | application procedure |
| 4 | customer insights |
| 4 | drilling |
| 4 | ecosystems |
| 4 | infectious diseases |
| 3 | clinical trials |
| 3 | banking |
| 3 | mechanics |
| 3 | transport |
| 3 | public health |
| 3 | pregnancy |
| 3 | designing |
| 3 | fuel |
| 3 | warehouse |
| 3 | sound |
| 3 | application process |
| 3 | android |
| 3 | databases |
| 3 | brands |
| 3 | cybersecurity |
| 3 | mathematics |
| 3 | statistics |
| 3 | computer science |
| 3 | biology |
| 3 | hr |

## Boundary errors (gold ⟶ overlapping predictions), top 40

| count | gold ⟶ pred |
|---|---|
| 13 | communication skills  ⟶  communication |
| 3 | Financial Services  ⟶  Financial |
| 2 | cloud adoption and migration  ⟶  migration |
| 2 | Financial Technology  ⟶  Financial |
| 2 | project management skills  ⟶  project management |
| 2 | property law rules of <LOCATION>  ⟶  property law |
| 2 | lead the next stage of development and strategy execution  ⟶  lead |
| 2 | English  ⟶  write English |
| 2 | European Data Protection Regulation  ⟶  Data Protection Regulation |
| 1 | build cloud native applications scratch  ⟶  scratch |
| 1 | enabling our clients to adapt to changing needs  ⟶  adapt to changing |
| 1 | communicate at all levels  ⟶  communicate |
| 1 | DevOps architecture and implementation  ⟶  DevOps |
| 1 | logging at scale  ⟶  logging |
| 1 | AWS DevOps Engineer or Azure DevOps Solution certification  ⟶  DevOps | DevOps |
| 1 | working within and leading multi-functional teams  ⟶  leading |
| 1 | develop services controls and patterns for cloud solutions  ⟶  patterns |
| 1 | enable security and privacy at scale  ⟶  security |
| 1 | work closely with product and design teams  ⟶  design |
| 1 | make sound sustainable and practical technical decisions  ⟶  sound |
| 1 | customer product and design focus  ⟶  design |
| 1 | reviewing technical solutions designs and requirements  ⟶  designs |
| 1 | mentor other team members  ⟶  mentor other |
| 1 | coaching and leading others  ⟶  leading others |
| 1 | work collaboratively in brainstorming sessions  ⟶  work collaboratively | brainstorming |
| 1 | promoting and advocating Agile and end to end CI/CD .  ⟶  Agile |
| 1 | DevOps best practices  ⟶  DevOps |
| 1 | RESTful web services  ⟶  web services |
| 1 | building RESTful web services  ⟶  web services |
| 1 | cloud hosting security practices  ⟶  security |
| 1 | hosting cost management  ⟶  cost management |
| 1 | software security  ⟶  security |
| 1 | designing robust systems  ⟶  designing |
| 1 | Enterprise Integration Patterns  ⟶  Patterns |
| 1 | Dimension Project Management  ⟶  Project Management |
| 1 | Leads technical solutions  ⟶  Leads |
| 1 | data and information  ⟶  information security |
| 1 | security  ⟶  information security |
| 1 | Leads the development tailoring and enhancement of cloud frameworks methods and tools  ⟶  Leads | tailoring |
| 1 | Leads the development of cloud transformation communications and education materials  ⟶  Leads | communications |

Total boundary-error gold spans: 311

## Gold spans with no overlapping prediction, top 40

| count | gold |
|---|---|
| 13 | aws |
| 11 | docker |
| 11 | node.js |
| 7 | react |
| 7 | linux |
| 7 | teaching |
| 7 | structured |
| 6 | amazon-web-services |
| 6 | kubernetes |
| 6 | software development |
| 6 | terraform |
| 6 | c |
| 5 | azure |
| 5 | gcp |
| 5 | html |
| 5 | reactjs |
| 4 | it consulting |
| 4 | cloud |
| 4 | hands-on |
| 4 | software development / engineering |
| 4 | software engineering |
| 4 | enthusiastic |
| 4 | supply chain |
| 3 | consulting |
| 3 | automation |
| 3 | monitoring |
| 3 | leadership |
| 3 | spring |
| 3 | artificial intelligence |
| 3 | team player |
| 3 | code reviews |
| 3 | motivation |
| 3 | curious |
| 3 | independent |
| 3 | technical insight |
| 3 | jquery |
| 3 | passionate |
| 3 | software architecture |
| 3 | analytical skills |
| 3 | open-minded |

Total fully-missed gold spans: 1604
