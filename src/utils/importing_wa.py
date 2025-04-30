from collections import defaultdict

import pandas as pd
from pandas import DataFrame
from whatstk import WhatsAppChat


def filter_messages(df, message_column="message"):
    """
    Filter out system messages and notifications from a DataFrame containing chat messages.

    Parameters:
    df (pandas.DataFrame): DataFrame containing the messages
    message_column (str): Name of the column containing the messages (default: 'message')

    Returns:
    pandas.DataFrame: DataFrame with filtered messages
    """
    # Create a copy to avoid modifying original
    filtered_df = df.copy()

    # Basic system messages
    system_patterns = [
        r"\bThis message was deleted\b",
        r"\byou deleted this message\.",
        r"\byou deleted this message as admin\b",
        r"\bContact card omitted\b",
        r"^GIF omitted\b",
        r"^image omitted$",
        r"^video omitted$",
        r"\bsecurity code\b",
        r"\bpinned a message\b",
        r"^Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.$",
        r"\b.* created this group$",
        r"\b.* created group .*",
        r"^New members need admin approval to join this group.",
        r"^.+ added .+$",
        r"^New members need admin approval to join this group.$",
        r"^New members need admin approval to join this group.$",
        r"^You added .+$",
        r"^.* added this group to the community: .+$",
        r"^sticker omitted$",
        r"^image omitted$",
        r"^This group has over 256 members so now only admins can edit the group settings$",
        r"^.+ changed this group’s settings to allow only admins to add others to this group.$",
        r"^.+ reset this group's invite link$",
    ]

    # Group membership patterns
    membership_patterns = [
        r"\b\d{3}[-‐]?\d{3,4}\s+left\b",
        r"\brequested to join\b",
        r"\bjoined using this group's invite link\b",
        r"^.* joined using your invite$",
        r"^.+ left$",
        r"^.* joined from the community$",
        r"^You turned off admin approval to join this group$",
        r"^.+ added .+",
        r".+ requested to add .+",
        r".+ added .+\. Tap to change who can add other members.",
        r".+ removed .+",
    ]

    # Group settings patterns
    settings_patterns = [
        r"^.+ changed this group's\b",
        r"^.+ changed the group .*$",
        r"^.+ changed the settings so only admins can edit the group settings\b",
    ]

    # Apply each filter group separately
    for patterns in [system_patterns, membership_patterns, settings_patterns]:
        pattern = "|".join(f"(?:{p})" for p in patterns)
        mask = ~filtered_df[message_column].str.contains(
            pattern, case=False, na=False, regex=True
        )
        filtered_df = filtered_df[mask]

    return filtered_df


def merge_contact_dfs(*dfs) -> DataFrame:
    """
    This function merges multiple contacts dataframes into a single dataframe, while keeping only unique values.
    It returns a dataframe of
    :param args:
    :return:
    """

    # our_jid,their_jid,first_name,full_name,push_name,business_name

    # First remove the our_jid from all the dataframes
    for df in dfs:
        df.drop(columns=["our_jid"], inplace=True, errors="ignore")

    # Merge the dataframes
    return pd.concat(dfs).drop_duplicates()


def match_and_rename_users(
    wa_chat: WhatsAppChat, contacts_df: DataFrame
) -> WhatsAppChat:
    dict_of_users = defaultdict(list)

    contacts_df.fillna("", inplace=True)

    for index, row in contacts_df.iterrows():
        phone_number = row["their_jid"].split("@")[0]
        # Using standard hyphen and handling variable length numbers
        long_number = f"+{phone_number[0:3]} {phone_number[3:5]}-{phone_number[5:8]}-{phone_number[8:]}"
        dict_of_users[phone_number].extend([long_number])

        if row["full_name"]:
            dict_of_users[phone_number].extend(
                [row["full_name"], f"~ {row['full_name']}"]
            )

        elif row["push_name"]:
            dict_of_users[phone_number].extend(
                [row["push_name"], f"~ {row['push_name']}"]
            )

    dict_of_users = {k: list(set(v)) for k, v in dict_of_users.items()}

    swapped_names = wa_chat.rename_users(mapping=dict_of_users)
    return swapped_names


def split_chats(df, time_column, gap_hours=2, overlap=5, min_size=25, max_size=200):
    df = df.sort_values(by=time_column).reset_index(drop=True)  # Sort by timestamp
    df[time_column] = pd.to_datetime(df[time_column])  # Ensure datetime format
    time_diff = df[time_column].diff().dt.total_seconds().div(3600)  # Convert to hours
    split_indices = time_diff[time_diff >= gap_hours].index  # Identify large gaps

    # Step 1: Initial Splitting
    segments = []
    prev_idx = 0

    for idx in split_indices:
        segments.append(df.iloc[prev_idx:idx])
        prev_idx = idx
    segments.append(df.iloc[prev_idx:])  # Add last segment

    # Step 2: Merge small segments
    merged_segments = []
    buffer = pd.DataFrame()

    for segment in segments:
        if len(buffer) < min_size:
            buffer = pd.concat([buffer, segment]).reset_index(drop=True)
        else:
            merged_segments.append(buffer)
            buffer = segment

    if not buffer.empty:
        merged_segments.append(buffer)

    # Step 3: Split large segments
    final_segments = []
    for segment in merged_segments:
        while len(segment) > max_size:
            final_segments.append(segment.iloc[:max_size])
            segment = segment.iloc[max_size:]
        if not segment.empty:
            final_segments.append(segment)

    # Step 4: Add overlap
    overlapped_segments = []
    for i, segment in enumerate(final_segments):
        if i > 0:
            segment = (
                pd.concat([final_segments[i - 1].iloc[-overlap:], segment])
                .drop_duplicates()
                .reset_index(drop=True)
            )
        overlapped_segments.append(segment)

    return overlapped_segments
