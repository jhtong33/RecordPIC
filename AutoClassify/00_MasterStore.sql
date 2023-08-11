--------------------------------------------------------------------------------
--Time: 2023-07-20; Jing-Hui Tong
--Count master area stores
--Input Table:
--  setopdata.mstbda_area,
--  setopdata.mstbda_store_m
--------------------------------------------------------------------------------


select pp.master_area_no, master_area_name, cnt from 
(select distinct master_area_no, SPLIT_PART(area_name,'---',1) as master_area_name
	 from setopdata.mstbda_area 
	where eff_date_to = '9999-12-31') as pp
left join
(select master_area_no, count(master_area_no) as cnt 
	from setopdata.mstbda_store_m 
	where eff_date_to = '9999-12-31'
	group by master_area_no) as mm 
on pp.master_area_no = mm.master_area_no

order by pp.master_area_no;