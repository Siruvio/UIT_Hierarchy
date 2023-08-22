import hierarchy as h


if __name__ == '__main__':
    input_file = "Data/Input.json"

    sorted_data = h.sorting(filename=input_file)
    print("Sort completed")

    object_tree = h.tree_construct(dataset=sorted_data, out_index=8, print_out=True)
    print("Tree fully built")



