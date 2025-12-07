import Auth from '@/components/Auth';
import ReportForm from '@/components/ReportForm';
import Image from 'next/image';

const AllFuckingThingsOnOneSinglePageXD = () => {
  return (
    <>
      <header className='relative z-1 flex h-20 w-full items-center justify-between bg-white px-6'>
        <div className='flex w-1/2 items-center justify-start gap-6'>
          <div className='flex items-center justify-center gap-2'>
            <Image
              src='/godlo.png'
              alt='godlo'
              width={1280}
              height={1506}
              className='size-12 object-contain'
            />
            <p className='text-xl font-bold'>gov.pl</p>
          </div>
          <div className='h-14 w-0.5 rounded-full bg-red-500'></div>
          <div>
            <p className='font-semibold text-neutral-500'>
              Serwis Rzeczypospolitej Polskiej
            </p>
          </div>
        </div>
        <div className='font-inter flex w-1/2 items-center justify-end gap-8 text-[12px] leading-3.5 font-semibold text-neutral-800'>
          <div>
            <Image
              src='/fe.jpg'
              alt='fundusze-europejskie'
              width={1010}
              height={576}
              className='w-30'
            />
          </div>
          <div className='flex items-center justify-center gap-2'>
            <Image
              src='/pl.png'
              alt='polska'
              width={2560}
              height={1600}
              className='w-15 border border-black'
            />
            <p>
              Rzeczpospolita <br /> Polska
            </p>
          </div>
          <div className='flex items-center justify-center gap-2'>
            <Image
              src='/eu.svg'
              alt='europe'
              width={810}
              height={540}
              className='w-14'
            />
            <p>
              Dofinansowane przez <br /> Unię Europejską
            </p>
          </div>
        </div>
      </header>
      <main className='flex h-full w-full justify-center'>
        <Auth />
        {/* <ReportForm /> */}
      </main>
    </>
  );
};

export default AllFuckingThingsOnOneSinglePageXD;
