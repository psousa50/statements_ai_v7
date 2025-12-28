DO $$
DECLARE
    target_email TEXT := 'USER_EMAIL_HERE';
    target_user_id UUID;
BEGIN
    SELECT id INTO target_user_id FROM users WHERE email = target_email;

    IF target_user_id IS NULL THEN
        RAISE EXCEPTION 'User with email % not found', target_email;
    END IF;

    RAISE NOTICE 'Deleting user: % (ID: %)', target_email, target_user_id;

    DELETE FROM transactions
    WHERE account_id IN (SELECT id FROM accounts WHERE user_id = target_user_id)
       OR counterparty_account_id IN (SELECT id FROM accounts WHERE user_id = target_user_id);
    RAISE NOTICE 'Deleted transactions';

    DELETE FROM statements
    WHERE account_id IN (SELECT id FROM accounts WHERE user_id = target_user_id);
    RAISE NOTICE 'Deleted statements';

    DELETE FROM file_analysis_metadata
    WHERE account_id IN (SELECT id FROM accounts WHERE user_id = target_user_id);
    RAISE NOTICE 'Deleted file_analysis_metadata';

    DELETE FROM enhancement_rules WHERE user_id = target_user_id;
    RAISE NOTICE 'Deleted enhancement_rules';

    DELETE FROM description_group_members
    WHERE group_id IN (SELECT id FROM description_groups WHERE user_id = target_user_id);
    RAISE NOTICE 'Deleted description_group_members';

    DELETE FROM description_groups WHERE user_id = target_user_id;
    RAISE NOTICE 'Deleted description_groups';

    DELETE FROM saved_filters WHERE user_id = target_user_id;
    RAISE NOTICE 'Deleted saved_filters';

    DELETE FROM refresh_tokens WHERE user_id = target_user_id;
    RAISE NOTICE 'Deleted refresh_tokens';

    DELETE FROM categories WHERE user_id = target_user_id;
    RAISE NOTICE 'Deleted categories';

    DELETE FROM accounts WHERE user_id = target_user_id;
    RAISE NOTICE 'Deleted accounts';

    DELETE FROM users WHERE id = target_user_id;
    RAISE NOTICE 'Deleted user';

    RAISE NOTICE 'Successfully deleted user % and all related data', target_email;
END $$;
