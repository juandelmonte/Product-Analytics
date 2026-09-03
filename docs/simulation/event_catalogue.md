# Event Catalogue

Every product event the simulation emits, with its properties and the business
process that produces it. The event name maps to one or more features for
adoption measurement.

## Event taxonomy

| Event name | Produced by | Type | Feature |
|------------|-------------|------|---------|
| `user_signup` | Signup form submitted | lifecycle | - |
| `account_created` | Account provisioned | lifecycle | - |
| `workspace_created` | First user names a workspace | activation | workspace |
| `project_created` | User creates a project | activation | projects |
| `membership_invited` | Owner invites a teammate | activation | collaboration |
| `task_created` | User creates a task | activity | tasks |
| `task_assigned` | User assigns a task | activity | tasks |
| `task_commented` | User comments on a task | activity | comments |
| `task_completed` | User marks a task done | activity / activation | tasks |
| `integration_connected` | User connects an integration | activity | integrations |
| `plan_changed` | Account changes plan | lifecycle | billing |

## Common properties (all events)

| Property | Type | Notes |
|----------|------|-------|
| `event_id` | string | stable dedup key |
| `event_at` | datetime | event time (client clock) |
| `source_updated_at` | datetime | when the source record was last written |
| `account_id` | string | group/account key |
| `user_id` | string | actor |
| `plan` | string | account's plan at event time |

## Event-specific properties

| Event | Extra properties |
|-------|------------------|
| `user_signup` | `email`, `country`, `channel` |
| `account_created` | `account_name`, `country`, `channel`, `initial_plan` |
| `workspace_created` | `workspace_id`, `workspace_name` |
| `project_created` | `workspace_id`, `project_id`, `project_name` |
| `membership_invited` | `invitee_email`, `role` |
| `task_created` | `workspace_id`, `project_id`, `task_id` |
| `task_assigned` | `task_id`, `assignee_id` |
| `task_commented` | `task_id`, `comment_length` |
| `task_completed` | `task_id`, `project_id`, `hours_to_complete` |
| `integration_connected` | `integration_type` (slack/github/google) |
| `plan_changed` | `from_plan`, `to_plan` |

## Activity vs lifecycle events

- **Activity events** (feed DAU/WAU, retention, feature adoption, journeys):
  `task_created`, `task_assigned`, `task_commented`, `task_completed`,
  `integration_connected`, `project_created`, `workspace_created`.
- **Lifecycle events** (feed new users/accounts, activation, conversion):
  `user_signup`, `account_created`, `membership_invited`, `plan_changed`.

## Feature mapping (for Feature Adoption Rate)

| Feature code | Events |
|--------------|--------|
| `workspace` | `workspace_created` |
| `projects` | `project_created` |
| `tasks` | `task_created`, `task_assigned`, `task_completed` |
| `comments` | `task_commented` |
| `integrations` | `integration_connected` |

## Journey (common user journey)

The canonical journey for `fct_user_journey`:

```
Signup → Workspace created → Project created → Task created → Task completed
```

Journey conversion is computed per user/account with event-time ordering,
allowing late-arriving events to backfill a step without re-ordering.
