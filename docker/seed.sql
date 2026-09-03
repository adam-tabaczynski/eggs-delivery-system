INSERT INTO providers (name, email)
VALUES ('Doorstep Eggs', 'provider@doorstep-eggs.local')
ON CONFLICT (email) DO NOTHING;
