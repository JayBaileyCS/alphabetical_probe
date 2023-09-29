def get_training_data_num_distinct_letters(num_distinct_letters, num_samples, embeddings, distinct_letters_dict, all_rom_token_indices):

    # Fetch indices for tokens that contain the specified number of letters
    positive_indices = distinct_letters_dict[num_distinct_letters]

    # Fetch indices for tokens that do not contain the specified number of letters
    # (by taking a set difference and then converting back to a list)
    negative_indices = list(set(all_rom_token_indices) - set(positive_indices))

    # Randomly sample from positive and negative indices to balance the dataset
    num_positive = min(num_samples // 2, len(positive_indices))
    num_negative = num_samples - num_positive

    sampled_positive_indices = random.sample(positive_indices, num_positive)
    sampled_negative_indices = random.sample(negative_indices, num_negative)

    # Combine sampled indices
    sampled_indices = sampled_positive_indices + sampled_negative_indices
    random.shuffle(sampled_indices)  # Shuffle combined indices for randomness in training

    # Extract corresponding embeddings and labels
    all_embeddings = embeddings[sampled_indices]
    all_labels = [1 if idx in positive_indices else 0 for idx in sampled_indices]

    return all_embeddings.clone().detach(), torch.tensor(all_labels).clone().detach()  
