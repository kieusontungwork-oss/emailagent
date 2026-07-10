### Phase 1: Project Breakdown                                                 
                                                                                 
  Before writing code, the AI needs to break your massive PRD into bite-sized,   
  actionable tasks.                                                              
                                                                                 
  1. Generate Epics and User Stories                                             
  You need to convert the PRD into an Agile backlog.                             
                                                                                 
  • Prompt to use:                                                               
  │ "Use the  bmad-create-epics-and-stories  skill. Read the PRD located at      
  │ _bmad-output/planning-artifacts/prds/prd-EmailAgentV2-2026-06-23/prd.md  and 
  │ the Architecture Spine at  _bmad-output/planning-                            
  │ artifacts/architecture/architecture-EmailAgentV2-2026-07-02/ARCHITECTURE-    
  │ SPINE.md . Break the MVP requirements down into Epics and User Stories."     
                                                                                 
                                                                                 
  2. Create a Sprint Plan                                                        
  Once the backlog is generated, you need to decide what to build first.         
                                                                                 
  • Prompt to use:                                                               
  │ "Use the  bmad-sprint-planning  skill. Review the epics and stories we just  
  │ created, and generate a sprint plan for Sprint 1. Focus on the foundational  
  │ features required to get the most basic version of the Email Agent working." 
                                                                                 
  ──────                                                                         
  ### Phase 2: The Development Loop (Repeat for each story)                      
                                                                                 
  Now you will execute the sprint plan one story at a time. Do not try to build  
  the whole app at once; focus on one specific story file.                       
                                                                                 
  Step A: Create the Context-Rich Story File
  BMad works best when a story is isolated into its own file with all the        
  necessary context (dependencies, architecture rules, UX rules).
  
  • Prompt to use:
  │ "Use the  bmad-create-story  skill. I want to work on the first story from   
  our
  │ Sprint 1 plan. Generate the dedicated story file for it."
  

  Step B: Implement the Code
  Once the story file is created (it will usually be saved in a  _bmad-          
  output/stories/  folder), you hand it off to the developer agent to write the  
  actual code.
  
  • Prompt to use:
  │ "Use the  bmad-dev-story  skill. Implement the story we just created. Follow 
  │ all the architectural constraints and conventions strictly. Write the code,  
  │ create the necessary files, and let me know when you are done."
  

  (Note: If you just need a quick bug fix, refactor, or a tiny feature without   
  going through the heavy story process, you can bypass this and just say: "Use  
  bmad-quick-dev  to add a login button to the header.")
  
  Step C: QA and Automated Tests
  Once the AI writes the code, you should have it generate tests to prove it     
  works.
  
  • Prompt to use:
  │ "Use the  bmad-qa-generate-e2e-tests  skill to write automated tests for the 
  │ feature you just implemented."
  

  Step D: Code Review
  Before you commit the code to your  dev  branch, have the AI scrutinize its own
  work for edge cases or architectural violations.
  
  • Prompt to use:
  │ "Use the  bmad-code-review  skill to review the code changes you just made.  
  │ Hunt for edge cases, security flaws, or places where the code deviates from  
  │ the Architecture Spine."
  
  ──────
  ### Summary of Best Practices for the Developer:
  
  1. Never skip the Spec/Story phase: AI hallucinates when given vague           
  instructions. The  bmad-create-story  skill ensures the AI has a rigid contract
  to follow before it writes a single line of code.
  2. Review the diffs: Even though the AI writes the code, the developer is      
  responsible for reviewing the file changes (diffs) to ensure they make sense.  
  3. Commit often: After successfully finishing Step D for a single story, run   
  git add .  and  git commit -m "feat: implement [story name]" . Do not do       
  multiple stories in a single commit.