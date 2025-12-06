import ReportForm from '@/components/ReportForm';
import Image from 'next/image';

const AllFuckingThingsOnOneSinglePageXD = () => {
  return (
    <>
      <header className='flex h-20 w-full items-center justify-start gap-6 bg-white px-6'>
        <div className='flex items-center justify-center gap-2'>
          <Image
            src='/godlo.png'
            alt='godlo'
            width={1280}
            height={1506}
            className='size-12'
          />
          <p className='text-xl font-bold'>gov.pl</p>
        </div>
        <div className='h-14 w-0.5 rounded-full bg-red-500'></div>
        <div>
          <p className='font-semibold text-neutral-500'>
            Serwis Rzeczypospolitej Polskiej
          </p>
        </div>
      </header>
      <main className='flex w-full justify-center pt-32 pb-8'>
        <ReportForm />
      </main>
    </>
  );
};

export default AllFuckingThingsOnOneSinglePageXD;
