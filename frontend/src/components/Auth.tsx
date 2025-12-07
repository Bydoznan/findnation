import ReportFormInput from '@/components/ReportFormInput';
import Image from 'next/image';

const Auth = () => {
  return (
    <section className='h-screen-wo-topbar flex w-full'>
      <div className='flex w-3/10 flex-col items-start justify-start px-16 pt-20'>
        <h1 className='font-bebas-neue mb-8 text-5xl font-bold text-neutral-800'>
          LOGOWANIE
        </h1>
        <form className='flex w-full flex-col items-start justify-start gap-4'>
          <input
            type='text'
            className='h-12 w-full rounded-md border-2 border-black px-2'
            placeholder='Login'
          />
          <input
            type='text'
            className='h-12 w-full rounded-md border-2 border-black px-2'
            placeholder='Hasło'
          />
          <button
            type='submit'
            className='bg-custom-red font-bebas-neue my-4 h-12 w-40 rounded-md text-xl font-bold text-white'>
            ZALOGUJ
          </button>
        </form>
      </div>
      <div className='relative z-0 w-7/10 overflow-hidden object-contain shadow-[0_0_10px_1px_black]'>
        <Image
          src='/auth_bg.png'
          alt='background'
          fill={true}
        />
      </div>
    </section>
  );
};

export default Auth;
