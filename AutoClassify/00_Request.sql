--------------------------------------------------------------------------------
--Time: 2023-08-08; Jing-Hui Tong
--Request the dataset to classify member based on PMA
--Input Table:
--  setopdata.member_member_x, 
--  datacenter.festival_config,
--  setopdata.pos_d_m_member,
--  setopdata.mstbda_store_m
--Output Table:
--	analysis.kmean_clustering_sample_v6 (L202)
--------------------------------------------------------------------------------


---- Setting variables
--DROP TABLE #variables;

create temporary table variables AS (
     select '2023-07-17'::date as startdate,    -- you need to set
            '7':: int as howlong_day,           -- you need to set
            (howlong_day-1)::int as inputday,
            DATEADD(day, inputday, startdate)::date as enddate
); 

---- Personal list create
with personallist as 
(select mid, 
        case when ( birthday <= '1900-01-01' or birthday = '1980-10-10' or birthday = '2019-01-01' ) then null
	        when datediff(year, birthday, getdate()) >= 100 then null
	        when datediff(year, birthday, getdate()) < 100 then datediff(year, birthday, getdate()) end as age,
        replace(home_city, '台', '臺') as home_city,
        gender as sex
        from setopdata.member_member_x
        where len(mid)>'2' 
        order by mid, age )
		
---- festival list create        
, festival as (
    select cast(count(1) as float) as cnt_festival from datacenter.festival_config 
     where (start_date between (select  startdate from variables) and (select enddate from variables) ) ) 

---- Product, CV list create
, cvlist as (
    SELECT distinct mid, pma_no_fin, sum(item_cont) OVER (PARTITION BY mid, pma_no_fin) AS qty, sum(item_cont) OVER (PARTITION BY mid) AS all_cnt, 
    round(cast(qty as float)/cast(all_cnt as float),3) as cv_ratio, round(cast(sum(mm_sales) OVER (PARTITION BY mid, pma_no_fin) as float)/cast(qty as float),2) as aov, cv_ratio*aov as cv
    FROM setopdata.pos_d_m_member     
    where (data_date between (select  startdate from variables) and (select enddate from variables))
     and job_id = '23'
     and pma_no_fin not in ('22', '62', '69', '70', '80', '81', '88', '96', '97', '98', '99', '100', '400')
     and mid in (select mid from personallist)
)

---- Pruchase time list create
, purchasetimelist as 
(select mid, pma_no_fin, case when weekday_freq >= weekend_freq then '1' else '0' end as weekday, 
                         case when weekday_freq <= weekend_freq then '1' else '0' end as weekend, 
                         midnight, morning, noon, afternoon, night                         
from (  select mid, pma_no_fin, weekday_cnt/(7-( select cnt_festival from festival )) as weekday_freq, 
                        weekend_cnt/( select cnt_festival from festival ) as weekend_freq, 
                        midnight, morning, noon, afternoon, night
from (  select mid, pma_no_fin, 
            cast( count(case when weekend_ornot = 'weekday' then 1 end ) as float) as weekday_cnt , 
            cast( count(case when weekend_ornot = 'weekend' then 1 end ) as float) as weekend_cnt , 
            count(case when hour = '21-04' then 1 end ) as midnight,
            count(case when hour = '05-10' then 1 end ) as morning, 
            count(case when hour = '11-14' then 1 end ) as noon, 
            count(case when hour = '15-16' then 1 end ) as afternoon, 
            count(case when hour = '17-20' then 1 end ) as night
from ( 
	select mid, pma_no_fin,
    case when data_date in (select start_date from datacenter.festival_config ) then 'weekend' else 'weekday' end as weekend_ornot,
    case when SUBSTRING(sale_time, 1, 2) between '05' and '10' then '05-10'
         when SUBSTRING(sale_time, 1, 2) between '11' and '14' then '11-14'
         when SUBSTRING(sale_time, 1, 2) between '15' and '16' then '15-16'
         when SUBSTRING(sale_time, 1, 2) between '17' and '20' then '17-20'
         when SUBSTRING(sale_time, 1, 2) between '21' and '24' then '21-04' 
         when SUBSTRING(sale_time, 1, 2) between '00' and '04' then '21-04' end as hour

     from setopdata.pos_d_m_member    
     where (data_date between (select  startdate from variables) and (select enddate from variables))
     and job_id = '23'
     and pma_no_fin not in ('22', '62', '69', '70', '80', '81', '88', '96', '97', '98', '99', '100', '400')
     and mid in (select mid from personallist)
     group by mid, rec_no, data_date, sale_time, pma_no_fin)
     group by mid, pma_no_fin ))
     group by mid, pma_no_fin, weekday_freq, weekend_freq, midnight, morning, noon, afternoon, night

)

----RFM list create 
, rfmlist as 
( select temp_r.mid, temp_r.pma_no_fin, rfm_recency, rfm_frequency, aov, sum_item as rfm_monetary_sum, sum_item/rfm_frequency as rfm_monetary   from (
    (select mid, pma_no_fin, count(distinct rec_no) as rfm_frequency from setopdata.pos_d_m_member 
     where (data_date between (select startdate from variables) and (select enddate from variables))
     and job_id = '23'
     and pma_no_fin not in ('22', '62', '69', '70', '80', '81', '88', '96', '97', '98', '99', '100', '400')
     and mid in (select mid from personallist) 
     group by mid, pma_no_fin) as ff
    left join
     (select mid, pma_no_fin, datediff(day,max(data_date), (select enddate from variables)) as rfm_recency from setopdata.pos_d_m_member 
     where (data_date between (select startdate from variables) and (select enddate from variables))
     and job_id = '23'
     and pma_no_fin not in ('22', '62', '69', '70', '80', '81', '88', '96', '97', '98', '99', '100', '400')
     and mid in (select mid from personallist) 
     group by mid, pma_no_fin) as temp_r
    on ff.mid = temp_r.mid and ff.pma_no_fin = temp_r.pma_no_fin
    left join 
    (
     select mid, pma_no_fin, aov, aov*qty as sum_item from cvlist
    ) as temp_f
    on ff.mid = temp_f.mid and ff.pma_no_fin = temp_f.pma_no_fin
)
group by temp_r.mid, temp_r.pma_no_fin, temp_r.rfm_recency, ff.rfm_frequency, temp_f.aov, temp_f.sum_item
)
----AREA list create 
, arealist  as 
	(select mid, pma_no_fin,
	       count(case when store_m.master_area_no = '01' then 1 end ) as area_01 , 
	       count(case when store_m.master_area_no = '02' then 1 end ) as area_02 , 
	       count(case when store_m.master_area_no = '03' then 1 end ) as area_03 , 
	       count(case when store_m.master_area_no = '04' then 1 end ) as area_04 , 
	       count(case when store_m.master_area_no = '05' then 1 end ) as area_05 , 
	       count(case when store_m.master_area_no = '06' then 1 end ) as area_06 , 
	       count(case when store_m.master_area_no = '07' then 1 end ) as area_07 , 
	       count(case when store_m.master_area_no = '09' then 1 end ) as area_09 , 
	       count(case when store_m.master_area_no = '10' then 1 end ) as area_10 , 
	       count(case when store_m.master_area_no = '11' then 1 end ) as area_11
	from 
		(select  mid, pma_no_fin, store_no from setopdata.pos_d_m_member  
		    where (data_date between (select startdate from variables) and (select enddate from variables))
		    and job_id = '23'
		    and pma_no_fin not in ('22', '62', '69', '70', '80', '81', '88', '96', '97', '98', '99', '100', '400')
		    and mid in (select mid from personallist)) as md
		left join 
		( select store_no, master_area_no 
		  from setopdata.mstbda_store_m where eff_date_to = '9999-12-31') as store_m
		  on md.store_no = store_m.store_no
		  group by mid, pma_no_fin
		)
		
--- clear_address and old & new store_no
,temp_activelist as 
((select mid, pma_no_fin, store_no, 
          case when temp1.city is null then store_m.city else temp1.city end as city from 
          (select  mid, pma_no_fin, md.store_no, city from
               ((select  mid, pma_no_fin, store_no from setopdata.pos_d_m_member  
                    where (data_date between (select  startdate from variables) and (select enddate from variables))
                    and job_id = '23'
                    and pma_no_fin not in ('22', '54', '55', '58', '62', '69', '70', '80', '81', '82', '88', '96', '97', '98', '99', '100', '200', '400')
                    and mid in (select mid from personallist) ) as md
               left join 
               (select store_no, replace(city, '台', '臺') as city from (
                    select store_no, address , 
                    case when addr_type in ('A_city_dist','B_city_dist','C_city_dist','D_city') then SUBSTRING(address,1,3) else 'X' end as city
                    from (
                    select  store_no, address, case when SUBSTRING(address,3,1) in ('縣','市') and SUBSTRING(address,5,1) in ('鄉','鎮','市','區') then 'A_city_dist'
                         when SUBSTRING(address,3,1) in ('縣','市') and SUBSTRING(address,6,1) in ('鄉','鎮','市','區') then 'B_city_dist'
                         when SUBSTRING(address,3,1) in ('縣','市') and SUBSTRING(address,7,1) in ('鄉','鎮','市','區') then 'C_city_dist'
                         when SUBSTRING(address,3,1) in ('縣','市') then 'D_city' else 'E_Otrs' end as addr_type,
						 row_number() over(partition by store_no order by eff_date_from desc) as srl   
                         from setopdata.mstbda_store_m where store_test_flag = '0') where srl = 1 )) as store_m
               on md.store_no = store_m.store_no)) as temp1
          left join 
          (select old_store_no, replace(city, '台', '臺') as city from (
               select old_store_no, address , 
                    case when addr_type in ('A_city_dist','B_city_dist','C_city_dist','D_city') then SUBSTRING(address,1,3) else 'X' end as city from (
                         select  old_store_no, address, case when SUBSTRING(address,3,1) in ('縣','市') and SUBSTRING(address,5,1) in ('鄉','鎮','市','區') then 'A_city_dist'
                              when SUBSTRING(address,3,1) in ('縣','市') and SUBSTRING(address,6,1) in ('鄉','鎮','市','區') then 'B_city_dist'
                              when SUBSTRING(address,3,1) in ('縣','市') and SUBSTRING(address,7,1) in ('鄉','鎮','市','區') then 'C_city_dist'
                              when SUBSTRING(address,3,1) in ('縣','市') then 'D_city' else 'E_Otrs' end as addr_type,
							  row_number() over(partition by store_no order by eff_date_from desc) as srl   
                              from setopdata.mstbda_store_m where store_test_flag = '0') where srl = 1 )) as store_m
          on temp1.store_no = store_m.old_store_no)
)
---- ActiveCity, area list create 
, active_arealist  as 
(select distinct mid, pma_no_fin, 
     case when count(pma_no_fin) over(partition by mid, pma_no_fin) = 1 then active_city else '跨縣市' end as city_new, 
     case when count(distinct active_area) = 1 then active_area else '跨區域' end as area_new 
     from 
     (select mid, pma_no_fin, city as active_city , count(city) as cnt_active_city, 
          max(cnt_active_city) over(partition by mid, pma_no_fin ) as max_cnt_city, 
          case when active_city in ('臺北市', '新北市', '基隆市', '新竹市', '桃園市', '新竹縣', '宜蘭縣') then '北部' 
               when active_city in ('臺中市', '苗栗縣', '彰化縣', '南投縣', '雲林縣') then '中部'
               when active_city in ('高雄市', '臺南市', '嘉義市', '嘉義縣', '屏東縣') then '南部' 
               when active_city in ('花蓮縣', '臺東縣') then '東部' 
               when active_city in ('金門縣', '連江縣', '澎湖縣') then '外島' end as active_area,
          count(active_area)  as cnt_active_area,
          max(cnt_active_area) over(partition by mid, pma_no_fin ) as max_cnt_area 
          from temp_activelist
          group by mid, pma_no_fin, active_city, active_area)
where cnt_active_area = max_cnt_area and cnt_active_city = max_cnt_city 
group by mid, pma_no_fin, active_city, active_area
)
		
		
--- left join all list 
select ccc.mid, ccc.pma_no_fin, qty, round(cast(qty as float)/cast(rfm_frequency as float),2) as avg_qty, 
    aov, cv_ratio, cv, rfm_recency, rfm_frequency, rfm_monetary_sum, rfm_monetary, 
    weekday, weekend, midnight, morning, noon, afternoon, night, 
    area_01, area_02, area_03, area_04, area_05, area_06, area_07, area_09, area_10, area_11, 
	city_new as active_city, area_new as active_region, 
    age, home_city, sex 
    into analysis.kmean_clustering_sample_v6
    from 
    (select  mid, pma_no_fin, qty, cv_ratio, aov, cv from cvlist) as ccc
    left join 
    (select mid, pma_no_fin, rfm_recency, rfm_frequency , rfm_monetary_sum, rfm_monetary from rfmlist) as rrr
    on ccc.mid = rrr.mid and ccc.pma_no_fin = rrr.pma_no_fin
    left join 
    (select mid, pma_no_fin, weekday, weekend, midnight, morning, noon, afternoon, night 
    from purchasetimelist) as purr
    on ccc.mid= purr.mid and ccc.pma_no_fin = purr.pma_no_fin
    left join 
    (select * from arealist) as area
    on area.mid = ccc.mid and ccc.pma_no_fin = area.pma_no_fin
    left join 
    (select * from active_arealist) as act_area
    on act_area.mid = ccc.mid and ccc.pma_no_fin = act_area.pma_no_fin
    left join 
    (select mid, age, home_city, sex from personallist) as ppp
    on ccc.mid = ppp.mid

    order by ccc.mid, ccc.pma_no_fin;