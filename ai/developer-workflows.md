# Developer Workflows

For each step that contains an instruction you change need to type an @ folowed by the name of the file containing the instructions

## Planning s story

1. Create a new chat
1. [load documentation into context](/ai/instructions/load-all-documentation-into-context.md)
1. [pick up next story](/ai/instructions/pick-up-next-story.md)
1. [create story plan](/ai/instructions/create-story-plan.md) - add external libraries documentation if needed (in Cursor use @docs)
1. Carefully review the plan, ask for changes if needed
1. [move plan to in progress](/ai/instructions/move-plan-to-in-progress.md)

## Development of story

1. Create a new chat
1. [load in progress to context](/ai/instructions/load-in-progress-to-context.md)
1. [implement story](/ai/instructions/implement-story.md) - add external libraries documentation if needed (in Cursor use @docs)
1. Carefully review each step, ask for changes if needed
1. [mark story as done](/ai/instructions/mark-story-as-done.md)

## New Story

1. Create a new chat
1. [load all the documentation into context](/ai/instructions/load-all-documentation-into-context.md)
1. [create a new story for the following requirements](/ai/instructions/create-new-story-for-the-following-requirements.md)
1. Carefully review the new story, ask for changes if needed
1. [save new story into user stories](/ai/instructions/save-new-story-into-user-stories.md)

## Refactoring

(TODO)

## Spike

(TODO)
