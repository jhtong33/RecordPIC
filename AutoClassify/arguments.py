
from argparse import ArgumentParser
from numpy import nan
import glob, os 
import pandas as pd

def get_arguments(argv=None):
    parser = ArgumentParser(
        usage="%(prog)s --file --pma",
        description="")
        
    parser.add_argument(
        "-f", "-F", "--file",
        action="store",
        type=str,
        dest="filename",
        default=None,
        help="Specify the file you input")    
        
    parser.add_argument(
        "--pma",
        action="store",
        type=int,
        dest="pma",
        default=None,
        help="Specify the PMA number to classify")
        
    parser.add_argument(
        "-m", "-M", "--method",
        action="store",
        type=str,
        dest="method",
        default="KMeans",
        help="Choose the method to classify. Options include: "+
        "'KMeans', 'KPrototypes', 'KMedoids', 'Kmodes'. [Default is 'Kmeans']")        
    parser.add_argument(
        "-c", "-C", "--category",
        action="store",
        type=str,
        dest="category",
        default=None,
        help="Select one or more features you want to include to classify. Options include:"+
        "'personal', 'rfm', 'area', 'purchasetime', 'prefer', 'calculated'. [Default is 'personal']") 
    parser.add_argument(
        "--category-json",
        action="store",
        type=str,
        dest="cate_json",
        default="category_config.json",
        help="Specify .json file to read the categories and correspond items. "+
        "[Default is './category_config.json']")       
    parser.add_argument(
        "-o", "-O", "--overwrite",
        action="store_true",
        dest="ovr",
        default=False,
        help="Force the overwriting of pre-existing results. " +
        "Default behaviour prompts for those that " +
        "already exist. Selecting overwrite and skip (ie, both flags) " +
        "negate each other, and both are set to " +
        "false (every repeat is prompted). [Default is False]")  
    parser.add_argument(
        "-v", "-V", "--verbose",
        action="store_true",
        dest="verb",
        default=False,
        help="Specify to increase verbosity. [Default is False]")        

    # Auto/Manual Settings
    AutoGroup = parser.add_argument_group(
        title="Auto Classify Settings",
        description="***** Settings associated with searching the best number of clusters")
    AutoGroup.add_argument(
         "-n", "-N", "--num",
        action="store",
        type=int,
        dest="numofCluster",
        default=None,
        help="Manunally specify the number of group. [Default is None]")
    AutoGroup.add_argument(
        "-a", "-A", "--auto", 
        action="store_true",
        dest="AutoCluster",
        default=False,
        help="If select this option, it will automatically search the "+
        "best number of clusters. [Default is False]")
    AutoGroup.add_argument(
        "--auto-method",
        action="store",
        type=str,
        dest="selectMethod",
        default="elbow",
        help="Choose the method to find the best number of cluster. Options include: "+
        "'elbow', 'calinski-harabasz', 'davies-bouldin', 'silhouette', 'bic'. [Default is 'elbow']")
    AutoGroup.add_argument(
         "--Gmin",
        action="store",
        type=int,
        dest="Gmin",
        default=2,
        help="Specify the minimum group. [Default is 2]") 
    AutoGroup.add_argument(
         "--Gmax",
        action="store",
        type=int,
        dest="Gmax",
        default=10,
        help="Specify the maximum group. [Default is 10]")        

    # RFM Settings
    RFMGroup = parser.add_argument_group(
        title="RFM level",
        description="***** If 'rfm' in category, settings how to distinguish the RFM level")
    RFMGroup.add_argument(
        "--rfm-level",
        action="store",
        type=str,
        dest="rfm_level",
        default="median",
        help="Selecting how to distinguish the level. "+
        "Options include: 'median', 'mode', 'average'. [Default is 'median']")
    RFMGroup.add_argument(
        "--rfm-select",
        action="store_true",
        dest="select_rfm",
        default=False,
        help="Choosing whether three elements to classify or not. [Default is False]")            
    RFMGroup.add_argument(
        "--rfm-select-two",
        action="store",
        type=str,
        dest="select_two",
        default=None,
        help="Choosing whether two elements to classify."+
        "Options include: 'r', 'f', 'm'. [Default is 'f','m']")       
    # Path Settings
    PathGroup = parser.add_argument_group(
        title="Path to save",
        description="Settings associated with saving the results after clustering.")
    PathGroup.add_argument(
        "-p", "-P", "--path",
        action="store",
        type=str,
        dest="savepath",
        default=".",
        help="The path to save the results. [Default is the path of this code]")  
        
    args = parser.parse_args(argv)  
    
    
    
    if len(args.filename) > 1:
        try:
            ifglob = len(glob.glob(args.filename))
            if ifglob < 1:
                parser.error(f"Cannot glob the file {args.filename}")
            else:
                df = pd.read_csv(args.filename)
                try:
                    for mustkey in ['mid', 'pma_no_fin', 'qty', 'avg_qty']:
                        if mustkey not in df.keys():
                            parser.error("***The file must contain columns: mid, pma_no_fin, qty, avg_qty")
                except:
                    parser.error("***The file must contains columns: mid, pma_no_fin, qty, avg_qty")
        except:
            parser.error(f"Cannot glob the file {args.filename}, please use --file=*.csv")
    else:
        parser.error(f"***MUST input the file, please use --file=*.csv")
    if args.pma == None: 
        parser.error("***MUST select one PMA number")
    elif args.pma in [22, 62, 69, 70, 80, 81, 88, 96, 97, 98, 99, 100, 400]:
        parser.error(f"PMA: {args.pma} is not useful category")
    
    
    if args.category is not None:
        args.category = args.category.split(',')
    
    if args.method not in ['KMeans', 'KPrototypes', 'KMedoids', 'Kmodes']:
        parser.error(f"Method: {args.method} is not in our options")
    
    
    if len(args.cate_json) > 1:
        try:
            df_cate = pd.read_json(args.cate_json)
            if 'key' not in df_cate.index:
                parser.error(f"{args.cate_json} must contain 'key'")
            elif 'format' not in df_cate.index:
                parser.error(f"{args.cate_json} must contain 'format'")
            elif args.category is not None:
                for inputcate in args.category:
                    if inputcate not in df_cate.keys():
                        parser.error(f"The category '{inputcate}' is not in {args.cate_json}")
        except:
            parser.error(f"Cannot glob {args.cate_json}")
        
    if args.AutoCluster and args.numofCluster is not None:
        parser.error(f"Please selece -a or -n to analyze. ")
    
    if args.selectMethod not in ['elbow', 'calinski-harabasz', 'davies-bouldin', 'silhouette', 'bic']:
        parser.error(f"Please check the option: --auto-method={args.selectMethod}")
        
        
    if args.rfm_level not in ['median', 'mode', 'average']:
        parser.error(f"Please check the option: --rfm-level={args.rfm_level}")
    
    if args.select_rfm == True and args.select_two is None:
        parser.error("Please select two elemets (option: --rfm-select-two)")
    elif args.select_rfm == True and args.select_two is not None:     
        args.select_two = args.select_two.rsplit(",")     
        if len(args.select_two) != 2 :
            parser.error(f"Please select two elemets from 'r','f','m', you input {len(args.select_two)} elemets")
        elif len(args.select_two) == 2 :
            if args.select_two[0] not in ['r','f','m']:
                parser.error("Please select two elemets from 'r','f','m'")
            elif args.select_two[1] not in ['r','f','m']:
                parser.error("Please select two elemets from 'r','f','m'")
             
            
    if args.savepath == '.':
        args.savepath = os.getcwd() 
    
    

    return args
    
       